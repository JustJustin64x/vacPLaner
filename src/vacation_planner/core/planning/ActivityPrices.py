"""Optional admission tariffs, separate from the accommodation/transport budget."""


def activity_price_text(offer):
    d=offer['details'];old='Gespeicherter Tarif veraltet · ' if offer.get('price_status')=='veraltet' else ''
    return old+('Bestätigt kostenloser allgemeiner Zugang' if d['kind']=='free_access' else 'Belegter veröffentlichter Eintritt: '+d['unit_price']+' EUR pro Erwachsenem')+' · Gruppe: '+offer['eur_amount']+' EUR · optional außerhalb des Hauptbudgets · '+d['period_note']+' · Abfrage '+offer['retrieved_at']


def apply_activity_price(trip,offer):
    details=offer['details'];name=details['activity_name']
    aliases={'Museum Goldenes Dachl':('museum goldenes dachl',),'Burg Bled':('burg bled','blejski grad','bled castle'),'National Gallery':('national gallery','the national gallery')}
    item=next((a for a in trip.get('activities',[]) if a.get('name','').casefold() in aliases.get(name,(name.casefold(),))),None)
    if item is None:
        item={'id':offer['identifier'],'name':name,'topics':details['topics'],'source':offer['source'],'url':offer['source'],
              'description':'Einrichtung mit offiziell veröffentlichtem Eintrittstarif.','duration':'Besuchsdauer offen','latitude':None,'longitude':None,
              'link_kind':'Offizielle Preisquelle','retrieved_at':offer['retrieved_at']}
        trip.setdefault('activities',[]).insert(0,item)
    item['activity_price']=offer
    item['retrieved_at']=offer['retrieved_at']
    item['price_status']=activity_price_text(offer)
