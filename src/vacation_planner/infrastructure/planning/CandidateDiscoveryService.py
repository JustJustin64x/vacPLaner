"""One optional local model call; exact local identities; bounded safe prefetch."""
import copy
import json
import time
from urllib.parse import quote
from ...core.planning.CandidateIdeas import IdeaReferences,reference_places,geographic_allowed,valid_name,MAX_DEEP
from ...core.planning.CandidateSelection import same_holiday_region
from ...core.planning.SearchContext import SearchContext
from ...core.planning.SourceEvidence import merge_research
from .DestinationCatalog import normalize
from .DestinationImportService import COUNTRIES
from .EuropeScope import contains
from .TripStore import timestamp
from .ResearchHttp import ResearchHttp
from .SourceResearchService import SourceResearchService
from .WikivoyageParser import WikivoyageParser
from ..local_ai.LocalModelClient import LocalModelClient
from ..local_ai.Validation import validate_json


class CandidateDiscoveryService:
    def __init__(self,catalog,store=None,client=None):self.catalog=catalog;self.store=store;self.client=client

    def suggest(self,candidates,chosen,results,request,origin,context,emit,diagnostic):
        report=dict(enabled=True,model_calls=0,proposed=0,resolved=0,rejected=0,deep_researched=0,returned_matches=0,returned_ideas=0,
                    source_targets=0,source_http_calls=0,budget_skipped=0,decisions=[],status='pending')
        diagnostic['ai_discovery']=report
        if context.calls>=context.budget or context.deadline-time.monotonic()<2:
            report.update(status='rest_budget_exhausted',budget_skipped=1);return []
        began=time.monotonic();deadline=min(context.deadline,began+35)
        check=SearchContext(context.cancel,seconds=max(.01,deadline-began),budget=0)
        try:
            refs=IdeaReferences(reference_places(self.catalog,candidates,chosen,results,request,origin,check))
            countries=[c for c in COUNTRIES if self.catalog.country_allowed(c,request)]
            client=self.client or LocalModelClient();report['model_calls']=1
            emit('phase','Lokale KI prüft wenige zusätzliche Zielideen; alle Angaben werden unabhängig aufgelöst')
            response=client.chat(refs.messages(request,[dict(name=d['name'],country=d['code']) for d in chosen[:16]]),schema=refs.schema(countries),cancel=context.cancel,
                timeout=min(20,max(.01,deadline-time.monotonic())))
            value=validate_json(response['parsed'],refs.schema(countries));ideas=value['ideas'];report['proposed']=len(ideas)
            accepted=[];seen={d['id'] for d in chosen}
            for idea in ideas:
                check.check();reason=None;d=None
                if not valid_name(idea['name']) or not (idea['region']=='' or valid_name(idea['region'])):reason='Ungültige Orts-/Regionsangabe'
                elif idea['reference']:
                    try:
                        d=copy.deepcopy(refs.resolve(idea))
                        if idea['region'] and self.catalog.area(idea['region']) not in self.catalog.labels(d):reason='Referenzregion nicht bestätigt'
                    except ValueError:reason='Fremde Referenz oder abweichende Ortsangaben'
                else:
                    if self.catalog.inventory:
                        matches=self.catalog.inventory.exact_named_places(idea['name'],idea['country'],idea['region'],check)
                    else:
                        matches=[p for p in self.catalog.destinations if p['code']==idea['country'] and normalize(idea['name']) in {normalize(p['name']),*(normalize(a) for a in p.get('aliases',[]))}
                                 and (not idea['region'] or self.catalog.area(idea['region']) in self.catalog.labels(p))]
                    if len(matches)!=1:reason='Ortsidentität fehlt oder ist mehrdeutig'
                    else:d=copy.deepcopy(matches[0])
                if not reason and (d.get('kind') not in (None,'settlement') or not contains(d['code'],d['latitude'],d['longitude'])):reason='Kein belegter europäischer Aufenthaltsort'
                if not reason and not geographic_allowed(self.catalog,d,request,origin):reason='Verbindliche Geografie-, Typ- oder Radiuskriterien verletzt'
                if not reason and (d['id'] in seen or any(same_holiday_region(d,t['destination']) for t in results) or any(same_holiday_region(d,p) for p in accepted)):reason='Bereits geprüft oder nahe Alternative derselben Urlaubsregion'
                label=idea['name'] if valid_name(idea['name']) else 'Ungültiger Vorschlag'
                if reason:
                    report['rejected']+=1;report['decisions'].append(dict(name=label,country=idea['country'],status='rejected',reason=reason));continue
                seen.add(d['id']);report['resolved']+=1
                if len(accepted)>=MAX_DEEP:
                    report['budget_skipped']+=1;report['decisions'].append(dict(name=d['name'],id=d['id'],status='not_deepened',reason='Zusätzliche Vertiefung auf zwei Orte begrenzt'));continue
                d['discovery_origin']=dict(kind='local_model_idea',identity_source=d['source'],identity_method='Aufrufreferenz zum lokalen Bestand' if idea['reference'] else 'Exakter Name/Alias und ISO-Land im vollständigen lokalen Landesbestand',
                    explanation='Zusätzliche KI-Idee, unabhängig geografisch zugeordnet. Interessen, Unterkunft und Verkehr werden regulär geprüft.')
                accepted.append(d);report['decisions'].append(dict(name=d['name'],id=d['id'],country=d['code'],status='resolved',reason='Eindeutige Bestandsidentität; keine Modellkoordinaten übernommen'))
            report['status']='resolved' if accepted else 'no_additional_verified_ideas'
            return accepted
        except InterruptedError:
            if context.cancel.is_set():raise
            report.update(status='rest_time_exhausted',budget_skipped=1);return []
        except (OSError,ValueError,TypeError,KeyError):
            report['status']='model_unavailable_or_invalid';emit('warning','KI-Zielideen nicht verfügbar oder nicht überprüfbar; vorhandene Suchergebnisse bleiben erhalten.');return []
        finally:report['seconds']=time.monotonic()-began

    def prepare(self,destination,request,context,emit,report):
        """One safe source target. No second model call, no unverified guide URLs."""
        if not self.store or report['source_targets']>=1 or context.calls>=context.budget or context.deadline-time.monotonic()<2:
            return destination,None
        report['source_targets']+=1
        child=SearchContext(context.cancel,seconds=min(35,max(.01,context.deadline-time.monotonic())),budget=min(6,context.budget-context.calls))
        candidate=copy.deepcopy(destination)
        candidate['wikivoyage_source']=destination.get('wikivoyage_source') or ('https://de.wikivoyage.org/wiki/'+quote(destination['name'].replace(' ','_'),safe=''))
        http=ResearchHttp(self.store);attempt=dict(attempted_at=timestamp(),status='failed',model_status='deterministische Quellenprüfung; kein weiterer Modellaufruf',gaps=[],message='')
        evidence=[]
        try:
            evidence,gaps=SourceResearchService(self.store,http).collect(dict(destination=candidate,request=request.to_dict()),child,emit)
            attempt['gaps']=gaps
            if evidence:
                candidate['wikivoyage_source']=evidence[0]['final_url']
                # Feed only the securely fetched verified page into the existing
                # normal adapter cache; don't refetch a guessed URL with another client.
                page=http.memory.get(candidate['wikivoyage_source'])
                if page:
                    parsed=WikivoyageParser().parse(page['body'].decode('utf-8'),dict(candidate,source=candidate['wikivoyage_source']),page['retrieved_at'])
                    self.store.cache_set('places-v4:'+candidate['wikivoyage_source'],parsed,page['retrieved_at'])
                elif not self.store.cache_get('places-v4:'+candidate['wikivoyage_source'],7*86400):
                    candidate.pop('wikivoyage_source',None) # extracted cache alone cannot trigger an unguarded refetch
                attempt.update(status='source_observations',message='Strukturierte Quellenbelege für regulär zu prüfenden Zusatzkandidaten')
            else:candidate=destination;attempt['status']='no_usable_observations'
        except InterruptedError:
            if context.cancel.is_set():raise
            candidate=destination;attempt.update(status='limited',message='Teilbudget erreicht; lokale Ortsidentität bleibt erhalten.')
        except (OSError,ValueError,TypeError,KeyError):
            candidate=destination;attempt['message']='Keine sicher zugeordnete zusätzliche Quelle verfügbar; keine URL oder Eignung aus Modellwissen übernommen.'
        finally:
            context.calls+=child.calls;context.disabled.update(child.disabled);report['source_http_calls']+=child.calls
            attempt['http_calls']=child.calls;attempt['elapsed_seconds']=time.monotonic()-child.started
        return candidate,dict(evidence=evidence,attempt=attempt)
