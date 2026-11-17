"""Beds24 guest selections, classic and bounded responsive contracts; no fixed IDs."""
import hashlib
import re
from datetime import datetime,timedelta
from urllib.parse import urlsplit,parse_qs,urlencode,urlunsplit
from bs4 import BeautifulSoup
from ...core.planning.TravelOffers import TravelOffer,amount
from .LodgingSourcePolicy import public_link


def control(node):
    if node.name=='select':
        o=node.select_one('option[selected]') or node.select_one('option')
        return o.get('value',o.get_text()) if o else ''
    return node.get('value','')


class UnsupportedVariant(ValueError):pass


class Beds24OfferAdapter:
    system='Beds24';variant='classic-guest-form-v1'

    @staticmethod
    def inventory(html,query):
        soup=BeautifulSoup(html,'html.parser')
        form=next((f for f in soup.select('form') if f.select_one('[name^="sr1-"]')),None)
        if form is None:raise UnsupportedVariant('Beds24-responsive, Anfrage- oder unbekannte Formularvariante; kein klassischer Bestandsvertrag')
        if form.get('method','get').lower()!='get' or form.get('action'):raise UnsupportedVariant('Unbekannte Formularaktion')
        values={n['name']:control(n) for n in form.select('input[name],select[name]')
                if n.get('type')!='submit' and (n.get('type')!='checkbox' or n.has_attr('checked'))}
        expected_date=values.get('checkin_hide') or values.get('firstnight') or values.get('fdate_monthyear','')+'-'+values.get('fdate_date','').zfill(2)
        if expected_date!=query.start or int(values.get('numnight','0'))!=(datetime.fromisoformat(query.end)-datetime.fromisoformat(query.start)).days:
            raise ValueError('Buchungsquelle hat andere Daten übernommen')
        rooms=[];fields=set()
        for selector in form.select('[name^="sr1-"]'):
            key=selector['name'];rid=key.split('-',1)[1]
            if not re.fullmatch(r'[1-9]\d{0,11}',rid):continue
            na=form.find(attrs={'name':'na1-'+rid});nc=form.find(attrs={'name':'nc1-'+rid})
            button=form.find(attrs={'name':'br1-'+rid})
            price=form.find(id='at_roomofferpriceofferid1-'+rid)
            if not na or not nc or not button or not price:continue
            if button.has_attr('disabled') or selector.has_attr('disabled') or 'at_dateavailable' not in price.get('class',[]):continue
            currency=price.select_one('.bookingpagecurrency')
            if not currency or currency.get_text(strip=True) not in ('€','EUR'):continue
            quantities=[int(o.get('value','0')) for o in selector.select('option') if o.get('value','').isdigit()]
            maximum=max(quantities,default=1 if selector.name=='input' else 0)
            if not maximum:continue
            count=int(na.get('value','0'))
            if not 1<=count<=40 or nc.get('value')!='0':continue
            rooms.append({'rid':rid,'maximum':maximum,'occupancy_max':count,'quantities':quantities or [0,1]})
            fields.update(prefix+'-'+rid for prefix in ('sr1','na1','nc1','br1'))
        if not rooms:raise UnsupportedVariant('Kein auswertbarer EUR-Zimmerbestand; keine negative Verfügbarkeitsaussage')
        return values,rooms,fields

    @staticmethod
    def combinations(rooms,occupancy,limit=4):
        """A type has one occupancy field: never mix occupancies in the same type."""
        results=[];visited=0
        def walk(index,chosen):
            nonlocal visited
            visited+=1
            if visited>512 or len(results)>=limit:return
            if index==len(occupancy):results.append(dict(chosen));return
            adults=occupancy[index]
            for r in rooms:
                old=chosen.get(r['rid']);qty=(old[0]+1 if old else 1)
                if adults>r['occupancy_max'] or qty not in r['quantities'] or (old and old[1]!=adults):continue
                chosen[r['rid']]=(qty,adults);walk(index+1,chosen)
                if old:chosen[r['rid']]=old
                else:chosen.pop(r['rid'])
        walk(0,{})
        unique=[]
        for x in results:
            if x not in unique:unique.append(x)
        return unique

    def search(self,query,item,base,http,policy,context,identity_verified=False):
        self.quote_responses=0
        p=urlsplit(base);ids={k:v[0] for k,v in parse_qs(p.query).items() if k in ('propid','ownerid','roomid')}
        if 'propid' not in ids:
            if 'ownerid' in ids:return self.owner_search(query,item,base,http,policy,context,identity_verified)
            raise UnsupportedVariant('Zimmerübersicht ohne eindeutig zugeordnetes Objekt')
        params=dict(ids,checkin=query.start,numnight=str((datetime.fromisoformat(query.end)-datetime.fromisoformat(query.start)).days),
                    numadult=str(query.adults),numchild=str(len(query.children_ages)),lang='de',multiroom='1')
        url=policy.query(base,params);record=http.fetch(url,context,types=('text/html',))
        html=record['body'].decode('utf-8')
        self.inventory_record=record
        soup=BeautifulSoup(html,'html.parser')
        if soup.select_one('form#formlook input[name="page"][value="book3"]'):
            return self.responsive(query,item,base,http,policy,context,params,ids,html,url,identity_verified)
        if query.children_ages:raise UnsupportedVariant('Klassische Quelle ohne unterstützten Kinder-Altersvertrag; keine Erwachsenenersatzsuche')
        values,rooms,fields=self.inventory(html,query)
        # Provider page, not the directory/site, must independently identify the property.
        from .LodgingWebsite import matches_identity
        if not matches_identity(item,html):raise ValueError('Buchungsobjekt passt nicht eindeutig zur Unterkunft')
        choices=self.combinations(rooms,query.occupancy)
        if not choices:raise UnsupportedVariant('Belegung nicht mit dem auswertbaren Bestand darstellbar; Verfügbarkeit bleibt offen')
        offers=[]
        for choice in choices[:1]:  # one source-validated quote per property/turn, fair shared budget
            context.check();q=dict(values)
            for r in rooms:q['sr1-'+r['rid']]='0'
            for rid,(qty,adults) in choice.items():q.update({'sr1-'+rid:str(qty),'na1-'+rid:str(adults),'nc1-'+rid:'0'})
            first=next(iter(choice));q['br1-'+first]='Buchen'
            quoted_url=policy.query(base,q,fields)
            quote=http.fetch(quoted_url,context,types=('text/html',))
            self.quote_responses+=1
            offer=self.parse_quote(quote['body'].decode('utf-8'),query,item,choice,quote['retrieved_at'],public_link(url),ids)
            self.quote_provenance(offer,quote);offers.append(offer)
        return offers

    def owner_search(self,query,item,base,http,policy,context,identity_verified):
        from .LodgingWebsite import extract_links,matches_identity
        self.variant='owner-property-list-v1'
        record=http.fetch(base,context,types=('text/html',));html=record['body'].decode('utf-8')
        candidates=[u for u in extract_links(html,record['final_url'])['booking'] if 'propid' in parse_qs(urlsplit(u).query)][:2]
        if not candidates:raise UnsupportedVariant('Betreiberübersicht ohne beobachtete Objektlinks; keine erfundenen Objektkennungen')
        errors=[];responses=0
        for candidate in candidates:
            context.check();target=policy.booking_link(candidate)
            self.quote_responses=0
            try:
                identity=http.fetch(target,context,types=('text/html',))
                if not matches_identity(item,identity['body'].decode('utf-8')):
                    errors.append('Einzelobjekt nicht durch Name und zusätzliche Identitätsmerkmale zugeordnet');continue
                offers=self.search(query,item,target,http,policy,context,identity_verified=True)
                for offer in offers:
                    offer.evidence['discovery_variant']='owner-property-list-v1'
                    offer.evidence['owner_source']={'url':public_link(record['final_url']),'retrieved_at':record['retrieved_at'],
                        'sha256':hashlib.sha256(record['body']).hexdigest(),'observed_property_url':public_link(target),
                        'identity_retrieved_at':identity['retrieved_at'],'identity_sha256':hashlib.sha256(identity['body']).hexdigest()}
                self.variant='owner-property-list-v1 / '+self.variant
                return offers
            except (ValueError,OSError) as exc:errors.append(str(exc))
            finally:
                responses+=self.quote_responses;self.quote_responses=responses
        self.variant='owner-property-list-v1'
        raise UnsupportedVariant('; '.join(errors) or 'Kein unabhängig zugeordnetes Einzelobjekt')

    @staticmethod
    def quote_provenance(offer,record):
        offer.evidence.update(quote_url=public_link(record['original_url']),final_quote_url=public_link(record['final_url']),
                              quote_sha256=hashlib.sha256(record['body']).hexdigest(),quote_retrieved_at=record['retrieved_at'])

    def responsive(self,query,item,base,http,policy,context,params,ids,html,url,identity_verified):
        from .Beds24ResponsiveQuote import Beds24ResponsiveQuote
        from .LodgingWebsite import matches_identity,matches_name
        self.variant= Beds24ResponsiveQuote.variant
        if not matches_identity(item,html) and not (identity_verified and matches_name(item,html)):
            raise ValueError('Responsives Buchungsobjekt nicht unabhängig zugeordnet')
        try:rooms,fields,multi=Beds24ResponsiveQuote.inventory(html,query)
        except ValueError as exc:raise UnsupportedVariant(str(exc)) from exc
        from .Beds24RoomSelection import selections
        choices=selections(rooms,query.room_assignments,limit=2,check=context.check)
        failures=[]
        for choice in choices:
            parameters=Beds24ResponsiveQuote.parameters(params,rooms,fields,multi,choice)
            quoted_url=policy.responsive_query(base,parameters,fields,multi)
            quote=http.fetch(quoted_url,context,types=('text/html',))
            self.quote_responses+=1
            try:
                offer=Beds24ResponsiveQuote.parse(quote['body'].decode('utf-8'),query,item,choice,quote['retrieved_at'],public_link(url),{'propid':ids['propid']},rooms)
                self.quote_provenance(offer,quote)
                if query.children_ages:
                    source=self.inventory_record
                    offer.evidence['child_age_source']={'url':public_link(source['final_url']),'retrieved_at':source['retrieved_at'],
                        'sha256':hashlib.sha256(source['body']).hexdigest(),'selector':'form#formlook label[for] / aria-label / title',
                        'labels':[c['label'] for c in offer.evidence['child_age_contracts']]}
                return [offer]
            except ValueError as exc:failures.append(str(exc))
        raise ValueError('Keine angenommene responsive Auswahlquote: '+'; '.join(failures or ['Belegung nicht darstellbar; keine negative Verfügbarkeitsaussage']))

    @staticmethod
    def parse_quote(html,query,item,choice,stamp,url,ids):
        soup=BeautifulSoup(html,'html.parser');form=soup.select_one('form#formbook')
        from .LodgingWebsite import matches_identity
        if not matches_identity(item,html):raise ValueError('Sichtbare Preisquote gehört nicht eindeutig zur Unterkunft')
        if form is None:raise ValueError('Keine bestätigte gemeinsame Zimmerauswahl; kein Ausgebucht-Nachweis')
        get=lambda key:form.find('input',attrs={'name':key})
        for key,expected in dict(ids,firstnight=query.start,checkout=query.end,numnight=str((datetime.fromisoformat(query.end)-datetime.fromisoformat(query.start)).days)).items():
            n=get(key)
            if n is None or n.get('value')!=expected:raise ValueError('Abweichender Zeitraum oder Unterkunft in Auswahlquote')
        confirmed=[];rows=form.select('.roomnamerow');total=amount(0)
        for row in rows:
            select=row.select_one('select[name^="sr1-"]')
            if select is None:raise ValueError('Zimmeranzahl in Quote fehlt')
            rid=select['name'].split('-',1)[1];qty=int(control(select))
            if not qty:continue
            adults=row.select_one('input[name="na1-'+rid+'"]')
            price=row.select_one('input[id$="roomprice"]');name=row.select_one('.at_roomnametext3')
            rendered=row.select_one('.b24pricecol .pricetdleft')
            icons=len(row.select('.at_peopleiconroomtype img'))
            if rid not in choice or adults is None or price is None or name is None or rendered is None:
                raise ValueError('Auswahlquote enthält unbelegte Zimmerbestandteile')
            if (qty,int(adults['value']))!=choice[rid] or icons!=choice[rid][1]:raise ValueError('Belegung in sichtbarer Auswahl weicht ab')
            line=amount(rendered.get_text(strip=True));unit=amount(price['value'])
            if line!=unit*qty:raise ValueError('Sichtbarer Zimmerbetrag widerspricht Stückzahl/Preis')
            total+=line;confirmed.append(dict(room_id=rid,quantity=qty,adults_per_unit=icons,name=name.get_text(' ',strip=True),total=str(line)))
        if {r['room_id'] for r in confirmed}!=set(choice) or sum(r['quantity'] for r in confirmed)!=query.rooms or sum(r['quantity']*r['adults_per_unit'] for r in confirmed)!=query.adults:
            raise ValueError('Gemeinsame Auswahl bestätigt nicht die vollständige Gruppe')
        shown=form.select_one('.book_totalprice');hidden=get('subtotalprice')
        if shown is None or hidden is None or amount(shown.get_text(strip=True))!=amount(hidden['value']) or total!=amount(hidden['value']):
            raise ValueError('Gesamtbetrag oder Pflicht-/Zusatzkosten nicht eindeutig normalisierbar')
        currency=form.select('.roomnamerow .currencytd')
        if not currency or any(n.get_text(strip=True) not in ('€','EUR') for n in currency):raise ValueError('Währung der Quote unklar')
        prop=dict(item);prop['id']=item['id'];prop['amenities']=dict(item.get('amenities',{}))
        if any(re.search(r'(?i)(gemeinschafts?bad|shared\s+bath)',r['name']) for r in confirmed):prop['amenities']['Eigenes Bad']=False
        identity=hashlib.sha256((item['id']+str(choice)+query.start+query.end).encode()).hexdigest()[:24]
        offer=TravelOffer('Beds24 · direkte Gastquelle','lodging','beds24:'+identity,url,stamp,query.to_dict(),str(total),'EUR','group_stay',str(total),
              valid_until=(datetime.fromisoformat(stamp)+timedelta(minutes=10)).isoformat(),
              details={'property':prop,'units':query.rooms,'capacity':query.adults,'nights':int(get('numnight')['value']),
                       'selected_rooms':confirmed,'board':'Optionale Leistungen nicht ausgewählt','cancellation':'Nicht unabhängig normalisiert'},
              evidence={'parameter_echo':{'start':query.start,'end':query.end,'rooms':confirmed,'property':ids},
                        'fees_complete':False,'normalization':'Gemeinsame sichtbare Auswahlquote; Zimmerzeilen und Gesamtbetrag unabhängig abgeglichen',
                        'original_total':shown.get_text(' ',strip=True),'system_variant':'classic-guest-form-v1'})
        from .Beds24QuoteEvidence import apply_room_evidence,room_facts
        room_evidence=[]
        for room in confirmed:
            facts,proof=room_facts(room['name'],'',query.start)
            room_evidence.append(dict(room_id=room['room_id'],room_text=room['name'],tariff_text='',facts=facts,proof=proof))
        apply_room_evidence(offer,room_evidence)
        offer.unresolved=['Vollständigkeit weiterer verpflichtender Gebühren nicht ausdrücklich belegt']
        if item['type']=='Ferienwohnung':offer.unresolved.append('Ausgewählte Buchungseinheiten; Anzahl getrennter Schlafzimmer nicht unabhängig belegt')
        return offer
