"""One ordinary price provider for every discovered property, with fair continuation."""
import copy
import hashlib
import time
from urllib.parse import urlsplit,parse_qs
from ...core.planning.LodgingResearch import initialize,summarize,finish
from ...core.planning.SearchContext import SearchContext
from ...core.planning.TravelOffers import OfferResult
from ...core.planning.OfferQuality import assess
from .ResearchHttp import ResearchHttp
from .LodgingSourcePolicy import LodgingSourcePolicy,public_link
from .LodgingWebsite import matches_identity,matches_name,extract_links,operator_links,availability_form
from .Beds24OfferAdapter import Beds24OfferAdapter,UnsupportedVariant
from .TripStore import timestamp


class LodgingOfferProvider:
    supports_child_ages=True
    name='Direkte Unterkunftsquellen';category='lodging'
    def __init__(self,store,emit=lambda *a:None,http_factory=None):
        self.store=store;self.emit=emit;self.http_factory=http_factory or (lambda policy:ResearchHttp(store,policy))

    def search(self,query,trip,context):
        ledger=initialize(trip);started=time.monotonic();before=context.calls;last_emit=0
        entries=ledger['entries'];continuing=getattr(context,'lodging_continue',False)
        terminal={'criteria_mismatch','no_booking_source','unsupported_variant','identity_uncertain','interaction_required','blocked'}
        def eligible(e):
            if e['state']=='criteria_mismatch' or (continuing and e['state'] in terminal) or e.get('retry_after',0)>time.time():return False
            if continuing and e.get('offers'):
                from datetime import datetime,timezone
                try:
                    if all((datetime.now(timezone.utc)-datetime.fromisoformat(o['retrieved_at'])).total_seconds()<600 for o in e['offers']):return False
                except (ValueError,KeyError,TypeError):pass
            return True
        candidates=[e for e in entries if eligible(e)]
        # Least-attempted first; neither budget restarts nor selection order starve later rows.
        candidates.sort(key=lambda e:(e['attempts'],e.get('last_attempt',''),
            urlsplit(e['lodging'].get('url','')).hostname not in LodgingSourcePolicy.BOOKING_HOSTS,e['id']))
        sources=[];interrupted=False
        for e in candidates[:64]:
            if e['state']=='criteria_mismatch':continue
            if e.get('offers') and continuing:
                from datetime import datetime,timezone
                try:fresh=all((datetime.now(timezone.utc)-datetime.fromisoformat(o['retrieved_at'])).total_seconds()<600 for o in e['offers'])
                except (ValueError,KeyError,TypeError):fresh=False
                if fresh:continue
            if e.get('retry_after',0)>time.time():continue
            child=SearchContext(context.cancel,seconds=min(90,max(.01,context.deadline-time.monotonic())),budget=min(12,max(0,context.budget-context.calls)))
            child.disabled.update(context.disabled)
            try:
                context.check()
                if child.budget<2:raise InterruptedError('Restbudget für weitere Unterkunftsprüfung unzureichend')
                e['attempts']+=1;e['state']='running'
                self.emit('phase',f"Unterkunft {e['lodging']['name']}: {e['stage']} · {context.calls}/{context.budget} Abfragen")
                old_offers=copy.deepcopy(e.get('offers',[]))
                self.check_property(e,query,trip,child)
                if old_offers and not e.get('offers'):e['previous_offers']=old_offers
            except InterruptedError as exc:
                finish(e,'cancelled' if context.cancel.is_set() else 'deferred_budget',str(exc))
                interrupted=context.cancel.is_set() or context.calls+child.calls>=context.budget or time.monotonic()>=context.deadline
            except UnsupportedVariant as exc:finish(e,'unsupported_variant',str(exc))
            except (OSError,ValueError,KeyError,TypeError) as exc:
                reason=str(exc);blocked=any(x in reason for x in ('Robots','HTTP 401','HTTP 403','HTTP 406','HTTP 429','Sperrantwort'))
                finish(e,'blocked' if blocked else 'source_error',reason)
                e['retry_after']=time.time()+900
            finally:
                context.calls+=child.calls;context.disabled.update(child.disabled)
                e['network_calls']+=child.calls;summarize(ledger)
                if time.monotonic()-last_emit>=.2 or interrupted:
                    self.emit('offer_partial',copy.deepcopy(trip));last_emit=time.monotonic()
            sources.extend([e.get('website',''),e.get('booking_url','')])
            if interrupted:break
        for e in entries:
            if e['state'] in ('pending','running'):
                finish(e,'cancelled' if context.cancel.is_set() else 'deferred_budget','Zeit-/Abruf-/Bearbeitungsbudget: noch nicht bearbeitet; Fortsetzen möglich')
        metrics=summarize(ledger)
        ledger['runs'].append({'at':timestamp(),'calls':context.calls-before,'seconds':round(time.monotonic()-started,3),'property_turn_limit':64,'metrics':copy.deepcopy(metrics)})
        ledger['runs']=ledger['runs'][-12:]
        # Only fresh current per-property quotes enter the existing price application.
        from datetime import datetime,timezone
        offers=[]
        for e in entries:
            for o in e.get('offers',[]):
                quality=assess(o,query,trip['request']);o['quality']=quality
                if quality['status'] not in ('outdated','mismatch','conflict'):offers.append(o)
        return OfferResult(self.name,self.category,'found' if offers else 'cancelled' if context.cancel.is_set() else 'unsupported',query.to_dict(),offers,
            message=f"{metrics['found']} gefunden · {metrics['official_websites']} Websites zugeordnet · {metrics['offer_checks']} Angebotsversuche · {len(offers)} aktuelle Teil-/Angebote; Einzelstatus in Unterkunftsprüfliste",
            sources=list(dict.fromkeys(public_link(s) for s in sources if s)))

    def check_property(self,e,query,trip,context):
        item=e['lodging'];url=item.get('url','')
        if not url or url==item.get('source') or urlsplit(url).hostname in ('www.openstreetmap.org','openstreetmap.org','de.wikivoyage.org'):
            finish(e,'no_booking_source','Verzeichnis enthält keinen zugeordneten offiziellen Website-Hinweis');return
        policy=LodgingSourcePolicy(url,item);http=self.http_factory(policy)
        cache_key='lodging-website-v2:'+hashlib.sha256((item['id']+'|'+url+'|'+str(item.get('identity_tags',{}))).encode()).hexdigest()
        owner_identity_pending=False
        cache=self.store.cache_get(cache_key,7*86400)
        if cache:
            info=cache[0];e.update(official_website=True,website=info['website'],website_checked_at=cache[1])
            for k in ('identity_source','identity_checked_at'):
                if info.get(k):e[k]=info[k]
            booking_links=info.get('bookings') or [info['booking']]
        else:
            seed=policy.seed;page=http.fetch(seed,context,types=('text/html',));html=page['body'].decode('utf-8')
            verified=matches_identity(item,html);links=extract_links(html,page['final_url'])
            booking_links=links['booking'];pages=links['pages'];systems=links['systems']
            if urlsplit(seed).hostname in policy.BOOKING_HOSTS:booking_links=[seed]
            # A directory may link straight to a backend whose header has no
            # address. Follow only its actual bounded operator anchors; the
            # operator must independently match the directory name + location.
            if not verified and booking_links==[seed] and matches_name(item,html):
                for link in operator_links(html,page['final_url']):
                    target=policy.operator_link(link,html,page['final_url'])
                    sub=http.fetch(target,context,types=('text/html',))
                    if matches_identity(item,sub['body'].decode('utf-8')):
                        verified=True;e['identity_source']=public_link(sub['final_url']);e['identity_checked_at']=sub['retrieved_at'];break
            if not booking_links:
                for link in pages[:2]:
                    context.check()
                    try:link=policy.site_link(link)
                    except ValueError:continue
                    sub=http.fetch(link,context,types=('text/html',));body=sub['body'].decode('utf-8')
                    verified=verified or matches_identity(item,body)
                    extra=extract_links(body,sub['final_url']);booking_links+=extra['booking'];systems+=extra['systems']
                    if not booking_links and verified and availability_form(body):
                        search=policy.availability_query(sub['final_url'],body,query)
                        searched=http.fetch(search,context,types=('text/html',))
                        results=extract_links(searched['body'].decode('utf-8'),searched['final_url'])
                        booking_links+=results['booking'];systems+=results['systems']
                    if booking_links:break
            if not verified:
                for link in links.get('identity_pages',[])[:1]:
                    target=policy.site_link(link)
                    contact=http.fetch(target,context,types=('text/html',))
                    if matches_identity(item,contact['body'].decode('utf-8')):
                        verified=True;e['identity_source']=public_link(contact['final_url']);e['identity_checked_at']=contact['retrieved_at'];break
            source_ids=parse_qs(urlsplit(seed).query)
            owner_identity_pending=(not verified and urlsplit(seed).hostname in policy.BOOKING_HOSTS and 'ownerid' in source_ids and 'propid' not in source_ids and matches_name(item,html))
            if not verified and not owner_identity_pending:
                finish(e,'identity_uncertain','Website nicht durch Name und zusätzliche Orts-/Adress-/Telefonmerkmale zugeordnet');return
            if verified:e.update(official_website=True,website=public_link(page['final_url']),website_checked_at=page['retrieved_at'])
            if not booking_links:
                if systems:
                    e.update(system=systems[0]['system'],variant=systems[0]['variant'],booking_url=public_link(systems[0]['url']))
                    finish(e,'unsupported_variant','Buchungslink erkannt, aber kein abgenommener Preis-/Bestandsadapter für dieses System');return
                finish(e,'no_booking_source','Im begrenzten Websiteumfang keine unterstützte Buchungsquelle; kein Verfügbarkeitsnachweis');return
            if not owner_identity_pending:self.store.cache_set(cache_key,dict(website=e['website'],booking=public_link(booking_links[0]),bookings=[public_link(b) for b in booking_links[:2]],
                identity_source=e.get('identity_source',''),identity_checked_at=e.get('identity_checked_at','')),page['retrieved_at'])
        failures=[];found=[]
        for link in booking_links[:2]:
            booking=policy.booking_link(link);e.update(booking_url=public_link(booking),stage='offer',system='Beds24')
            adapter=Beds24OfferAdapter();e['variant']=adapter.variant;e['offer_checks']+=1
            try:
                found=adapter.search(query,item,booking,http,policy,context,identity_verified=True)
                e['variant']=adapter.variant
                if owner_identity_pending and found:
                    proof=found[0].evidence['owner_source']
                    e.update(official_website=True,website=proof['observed_property_url'],website_checked_at=proof['retrieved_at'],identity_source=proof['observed_property_url'])
                break
            except InterruptedError:raise
            except (ValueError,OSError) as exc:
                e['variant']=adapter.variant
                failures.append({'source':public_link(booking),'reason':str(exc),'at':timestamp(),'kind':'unsupported_variant' if isinstance(exc,UnsupportedVariant) else 'rejected_response'})
                e['rejected_responses']=(e.get('rejected_responses',[])+[failures[-1]])[-8:]
            finally:
                e['selection_responses']=e.get('selection_responses',0)+getattr(adapter,'quote_responses',0)
        if not found:
            if failures and all(f['kind']=='unsupported_variant' for f in failures):raise UnsupportedVariant('; '.join(f['reason'] for f in failures))
            raise ValueError('; '.join(f['reason'] for f in failures))
        for o in found:
            o.quality=assess(o.to_dict(),query,trip['request'])
        e['offers']=[dict(o.to_dict(),quality=o.quality) for o in found]
        verified=any(o.quality['status']=='verified' for o in found)
        finish(e,'confirmed' if verified else 'partial','Gemeinsame Auswahlquote geprüft; keine Buchung. '+('Pflichtgesamtpreis belegt' if verified else 'Weitere Pflichtangaben fehlen; siehe Belege'))
