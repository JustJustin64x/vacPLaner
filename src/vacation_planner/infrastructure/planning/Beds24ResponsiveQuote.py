"""Read-only responsive guest selection. Never submit the returned guest form.

Room/offer IDs and selector ranges come from the delivered form. Its quantities
are candidates, not stock evidence: only a positive complete server selection
with matching panels, occupancy, dates and total can become a partial offer.
"""
import hashlib
import re
import json
from datetime import datetime,timedelta,date
from bs4 import BeautifulSoup
from ...core.planning.TravelOffers import TravelOffer,amount
from .LodgingWebsite import matches_name
from .Beds24RoomSelection import selection_rows
from .Beds24QuoteEvidence import child_age_contract,inventory_evidence,room_facts,apply_room_evidence
from ...core.planning.RoomParty import RoomParty
from collections import Counter


class Beds24ResponsiveQuote:
    variant='responsive-selection-v1'

    @staticmethod
    def inventory(html,query):
        soup=BeautifulSoup(html,'html.parser');form=soup.select_one('form#formlook')
        if not form or form.get('method','get').lower()!='get' or form.get('action'):
            raise ValueError('Kein unterstütztes responsives Gast-Auswahlformular')
        page=form.select_one('input[name="page"]')
        if not page or page.get('value')!='book3':raise ValueError('Unbekannter responsiver Formularschritt')
        dates=[]
        for name in ('checkindefault','checkoutdefault'):
            m=re.search(r'\b'+name+r'\s*=\s*new Date\(\s*(\d{4}),\s*(\d{1,2}),\s*(\d{1,2}),',html)
            if not m:raise ValueError('Quellendatum nicht unabhängig auswertbar')
            dates.append(f'{int(m[1]):04}-{int(m[2])+1:02}-{int(m[3]):02}')
        if dates!=[query.start,query.end]:raise ValueError('Responsive Quelle hat andere Daten übernommen')
        age_contract=child_age_contract(html,query)
        def candidate(offer,rid):
            # Published calendars prune candidates only. They never establish
            # a group quote; the final server selection remains mandatory.
            pattern=r'\$\("#ajaxroomoffer'+re.escape(offer+'-'+rid)+r'"\)\.data\("avail",\s*(\{[^;]+\})\)'
            match=re.search(pattern,html)
            if not match:return True
            try:calendar=json.loads(match[1])
            except ValueError:return False
            day=date.fromisoformat(query.start);end=date.fromisoformat(query.end)
            while day<end:
                if int(calendar.get(day.strftime('%Y%m%d'),0))%4!=1:return False
                day+=timedelta(days=1)
            return True
        rooms=[];fields=set()
        for n in form.select('select[name]'):
            m=re.fullmatch(r'sr([1-9]\d?)-(\d{1,12})',n['name'])
            if not m or n.has_attr('disabled'):continue
            offer,rid=m.groups();prefix=f'{offer}-{rid}'
            if not candidate(offer,rid):continue
            adult=form.find(attrs={'name':'naa1-'+prefix})
            if adult is None:continue
            adults=[int(o.get('value','-1')) for o in adult.select('option') if o.get('value','').isdigit() and not o.has_attr('disabled')]
            quantities=[int(o['value']) for o in n.select('option[value]') if o['value'].isdigit() and not o.has_attr('disabled')]
            if not adults or not quantities:continue
            quantities=[q for q in quantities if q<=40]
            if not quantities:continue
            unit_options={}
            for index in range(1,max(quantities)+1):
                adult_control=form.find(attrs={'name':f'naa{index}-{prefix}'})
                child_control=form.find(attrs={'name':f'ncc{index}-{prefix}'})
                def options(control):
                    if control is None or control.has_attr('disabled'):return []
                    return [int(o['value']) for o in control.select('option[value]') if o['value'].isdigit() and not o.has_attr('disabled') and int(o['value'])<=40]
                unit_options[index]={'adults':options(adult_control),'children':options(child_control) if child_control is not None else [0]}
            evidence=inventory_evidence(soup,rid,offer,query.start)
            if any(evidence['facts'].get(k) is False for k in query.required_amenities):continue
            rooms.append(dict(rid=rid,offer=offer,quantities=quantities,maximum=max(quantities),occupancy_max=max(adults),adults=adults,unit_options=unit_options,age_contract=age_contract,room_evidence=evidence))
            fields.add(n['name'])
            for control in form.select('[name]'):
                if re.fullmatch(r'(naa|ncc)\d+-'+re.escape(prefix),control['name']):fields.add(control['name'])
        multi=form.find(attrs={'name':'bookmult'})
        if rooms and multi:return rooms[:24],fields,True
        if multi:raise ValueError('Für den Zeitraum keine auswertbaren Kalenderkandidaten; Buchungshorizont oder Verfügbarkeit offen')
        # Single-room layouts use a source-delivered offer submit button.
        if query.rooms!=1:raise ValueError('Quelle stellt keine Mehrzimmerauswahl bereit; nicht ausgebucht')
        rooms=[];fields=set()
        for n in form.select('input[name]'):
            m=re.fullmatch(r'br([1-9]\d?)-(\d{1,12})',n['name'])
            if m and not n.has_attr('disabled'):
                offer,rid=m.groups()
                if not candidate(offer,rid):continue
                evidence=inventory_evidence(soup,rid,offer,query.start)
                if any(evidence['facts'].get(k) is False for k in query.required_amenities):continue
                rooms.append(dict(rid=rid,offer=offer,quantities=[0,1],maximum=1,occupancy_max=query.adults,adults=[query.adults],unit_options={1:{'adults':[query.adults],'children':[len(query.children_ages)]}},age_contract=age_contract,room_evidence=evidence))
                fields.add(n['name'])
        if not rooms:raise ValueError('Keine auswertbare responsive Zimmerauswahl')
        return rooms[:24],fields,False

    @staticmethod
    def parameters(params,rooms,fields,multi,choice):
        result=dict(params)
        selected=selection_rows(choice,rooms)
        if multi:
            result.update(page='book3',bookmult='')
            for room in rooms:result['sr'+room['offer']+'-'+room['rid']]='0'
            for row in selected:
                room=next(r for r in rooms if r['rid']==row.room_id and r['offer']==row.offer_id);suffix=row.offer_id+'-'+row.room_id
                result['sr'+suffix]=str(row.quantity)
                if row.quantity not in room['quantities']:raise ValueError('Unbelegte Zimmermenge')
                for index,party in enumerate(row.parties,1):
                    limits=room['unit_options'].get(index,{})
                    if party.adults not in limits.get('adults',[]) or len(party.children_ages) not in limits.get('children',[]):raise ValueError('Unbelegte Einheitenbelegung')
                    key=f'naa{index}-{suffix}'
                    if key not in fields:raise ValueError('Belegungsfeld fehlt')
                    result[key]=str(party.adults)
                    child=f'ncc{index}-{suffix}'
                    if child in fields:result[child]=str(len(party.children_ages))
                    elif party.children_ages:raise ValueError('Kinderfeld fehlt')
        else:
            if len(selected)!=1 or selected[0].quantity!=1:raise ValueError('Quelle unterstützt nur eine Einzelzimmerauswahl')
            row=selected[0];result['br'+row.offer_id+'-'+row.room_id]='Book'
        return result

    @classmethod
    def parse(cls,html,query,item,choice,stamp,url,ids,inventory=()):
        soup=BeautifulSoup(html,'html.parser');form=soup.select_one('form#formbook')
        if not form or not matches_name(item,html):raise ValueError('Keine eindeutig zugeordnete responsive Auswahlquote')
        def value(key):
            nodes=form.select('input[name="'+key+'"]')
            if len(nodes)!=1:raise ValueError('Fehlendes/mehrdeutiges Quotenfeld: '+key)
            return nodes[0].get('value','')
        nights=(datetime.fromisoformat(query.end)-datetime.fromisoformat(query.start)).days
        for key,expected in dict(ids,firstnight=query.start,checkout=query.end,numnight=str(nights),page='book').items():
            if value(key)!=expected:raise ValueError('Objekt/Zeitraum der Quote weicht ab')
        detail=form.select_one('.b24-bookingdetails .panel-body')
        if not detail:raise ValueError('Sichtbare Auswahldetails fehlen')
        selections=detail.select('input[name^="sr"]');confirmed=[];total=amount(0);seen=set()
        expected={ (r.room_id,r.offer_id):list(r.parties) for r in selection_rows(choice) }
        source_evidence=[]
        if query.children_ages:
            contracts=[r.get('age_contract') for r in inventory if (r['rid'],r['offer']) in expected]
            from ...core.planning.ChildAgeRange import ChildAgeRange
            if not contracts or any(not c or not ChildAgeRange(c['minimum'],c['maximum'],c['label']).accepts(query.children_ages) for c in contracts):raise ValueError('Kinder-Altersvertrag nicht nachgewiesen')
        # Each source selection has a corresponding xNroomprice and xNdrprice.
        for n in selections:
            m=re.fullmatch(r'sr([1-9]\d?)-(\d{1,12})-(\d{1,2})',n['name'])
            if not m:raise ValueError('Unbekannte Zimmerzeile')
            offer,rid,index=m.groups();qty=int(n.get('value','0'))
            if not qty:continue
            if not 1<=qty<=query.rooms:raise ValueError('Unzulässige Zimmermenge')
            key=(rid,offer)
            if key not in expected or (rid,offer,index) in seen:raise ValueError('Unbelegte/mehrdeutige Zimmerauswahl')
            seen.add((rid,offer,index));adults=int(value(f'na{offer}-{rid}-{index}'));children=int(value(f'nc{offer}-{rid}-{index}'))
            matched=[]
            for _ in range(qty):
                party=next((p for p in expected[key] if p.adults==adults and len(p.children_ages)==children),None)
                if party is None:raise ValueError('Zimmerbelegung weicht ab')
                expected[key].remove(party);matched.append(party)
            hidden=detail.select_one(f'#x{index}roomprice');shown=detail.select_one(f'#x{index}drprice')
            if not hidden or not shown:raise ValueError('Kein positiver sichtbarer Zimmerpreis; Auswahl nicht verfügbar oder ungeklärt')
            unit=amount(hidden['value']);line=amount(shown.get_text(strip=True))
            if unit<=0 or line!=unit*qty:raise ValueError('Zimmerpreis/-menge widersprüchlich')
            # Partition the actual panel at the next sr input; names and icons must match.
            start=list(detail.descendants).index(n);following=list(detail.descendants)[start:]
            fragment=[]
            for node in following[1:]:
                if getattr(node,'name',None)=='input' and re.fullmatch(r'sr\d+-\d+-\d+',node.get('name','')):break
                fragment.append(node)
            icons=sum('occupancyadult' in getattr(x,'attrs',{}).get('class',[]) for x in fragment)
            child_icons=sum('occupancychild' in getattr(x,'attrs',{}).get('class',[]) for x in fragment)
            if icons!=adults or child_icons!=children:raise ValueError('Sichtbare Personenbelegung weicht ab')
            name=next((x.get_text(' ',strip=True) for x in fragment if 'at_roomnametext' in getattr(x,'attrs',{}).get('class',[])),None)
            if not name:raise ValueError('Zimmername fehlt')
            def text_of(css):
                return next((x.get_text(' ',strip=True) for x in fragment if css in getattr(x,'attrs',{}).get('class',[])),'')
            terms=text_of('at_offersummary');tariff=text_of('at_offername')
            evidence=next((dict(r['room_evidence']) for r in inventory if r['rid']==rid and r['offer']==offer),dict(room_id=rid,offer_id=offer,room_text=name,tariff_text='',facts={},proof={}))
            final_facts,proof=room_facts(name,terms if len(terms)<=3000 else '',query.start)
            facts=dict(evidence['facts'])
            for feature,val in final_facts.items():
                if feature in facts and facts[feature]!=val:raise ValueError('Widersprüchliche Zimmer-/Tarifbedingungen')
                facts[feature]=val
            evidence.update(facts=facts,quote_terms=terms[:3000],quote_terms_truncated=len(terms)>3000)
            evidence['proof']=dict(evidence.get('proof',{}),**proof);source_evidence.append(evidence)
            total+=line;confirmed.append(dict(room_id=rid,offer_id=offer,quantity=qty,adults_per_unit=adults,
                children_ages_per_unit=[list(p.children_ages) for p in matched],name=name,total=str(line),tariff_name=tariff[:300],source_terms=terms[:3000],terms_truncated=len(terms)>3000))
        if any(expected.values()) or sum(x['quantity'] for x in confirmed)!=query.rooms:
            raise ValueError('Keine vollständige Gruppenauswahl')
        mandatory=[]
        for n in detail.select('input[id$="oblig"]'):
            m=re.fullmatch(r'x(\d+)oblig',n['id']);shown=detail.select_one('#x'+m[1]+'dispprice') if m else None
            if not shown or amount(n['value'],allow_negative=True)!=amount(shown.get_text(strip=True),allow_negative=True):raise ValueError('Pflichtzuschlag nicht abgleichbar')
            fee=amount(n['value'],allow_negative=True);total+=fee
            parent=shown.find_parent(id=re.compile(r'^zupsellrow'))
            label=parent.select_one('.b24-upsellname') if parent else None
            mandatory.append({'label':label.get_text(' ',strip=True) if label else 'Verpflichtender Quellenzuschlag','amount':str(fee),'included_in_total':True})
        shown=form.select_one('#totaldispprice')
        if not shown or total!=amount(shown.get_text(strip=True)) or total!=amount(value('subtotalprice')):raise ValueError('Gruppen-/Aufenthaltssumme widersprüchlich')
        currencies=detail.select('.bookingpagecurrency,.bookingpagecurrency2')
        if not currencies or any(n.get_text(strip=True) not in ('€','EUR') for n in currencies):raise ValueError('Währung unklar')
        identity=hashlib.sha256((item['id']+str(choice)+query.start+query.end).encode()).hexdigest()[:24]
        offer=TravelOffer('Beds24 · direkte Gastquelle','lodging','beds24:'+identity,url,stamp,query.to_dict(),str(total),'EUR','group_stay',str(total),
            valid_until=(datetime.fromisoformat(stamp)+timedelta(minutes=10)).isoformat(),
            details={'property':dict(item),'units':query.rooms,'capacity':query.persons,'nights':nights,'selected_rooms':confirmed,
                     'included_surcharges':mandatory,'board':'Nicht unabhängig normalisiert','cancellation':'Nicht unabhängig normalisiert'},
            evidence={'parameter_echo':{'start':query.start,'end':query.end,'rooms':confirmed,'property':ids},'fees_complete':False,
                      'normalization':'Gemeinsame responsive Auswahl; sichtbare Zeilen, Belegung, Pflichtzuschläge und Gesamtsumme abgeglichen',
                      'original_total':shown.get_text(strip=True),'system_variant':cls.variant})
        if query.children_ages:offer.evidence['child_age_contracts']=contracts
        apply_room_evidence(offer,source_evidence)
        offer.unresolved=['Vollständigkeit weiterer verpflichtender Gebühren und örtlicher Abgaben nicht ausdrücklich belegt']
        if item['type']=='Ferienwohnung':offer.unresolved.append('Buchungseinheiten; getrennte Schlafzimmer nicht unabhängig belegt')
        return offer
