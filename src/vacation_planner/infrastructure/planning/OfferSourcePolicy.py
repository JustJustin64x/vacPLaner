"""Only existing, read-only price adapters; no model-supplied destinations."""
from datetime import date
import re
from urllib.parse import parse_qs

PAGES={
 'www.apartments-innsbruck.com':{'/en/buchen/'},
 'www.innsbruck.gv.at':{'/freizeit/kultur/museen-stadtarchiv/museum-goldenes-dachl'},
 'www.blejski-grad.si':{'/sl/nacrtuj-obisk/cenik/'},
 'www.nationalgallery.org.uk':{'/visiting/plan-your-visit'},
 'futurium.de':{'/de/besuch'},
 'regiojet.com':{'/'},
}
HOSTS=set(PAGES)|{'booking.smoobu.com','brn-ybus-pubapi.sa.cz'}


def allowed(p):
    if p.hostname not in HOSTS:return False
    if p.path=='/robots.txt' and not p.query:return True
    if p.path in PAGES.get(p.hostname,set()) and not p.query:return True
    q=parse_qs(p.query,keep_blank_values=True,strict_parsing=True)
    if any(len(v)!=1 for k,v in q.items() if k!='tariffs'):return False
    def numbers(*keys):return all(re.fullmatch(r'[1-9]\d{0,11}',q.get(k,[''])[0]) for k in keys)
    if p.hostname=='booking.smoobu.com' and p.path=='/perfect-lodgings/checkAvailability':
        if set(q)!={'theme','arrivalDate','departureDate','userId','guests','adults','children'}:return False
        if q['theme']!=['booking-tool'] or q['userId']!=['71379'] or q['children']!=['0'] or q['guests']!=q['adults']:return False
        if not numbers('adults') or not 1<=int(q['adults'][0])<=40:return False
        return all(re.fullmatch(r'\d{2}\.\d{2}\.\d{2}',q[k][0]) for k in ('arrivalDate','departureDate'))
    if p.hostname=='brn-ybus-pubapi.sa.cz':
        if p.path=='/restapi/consts/locations' and not q:return True
        if not 1<=len(q.get('tariffs',[]))<=40 or set(q['tariffs'])!={'REGULAR'}:return False
        if p.path=='/restapi/routes/search/simple':
            if set(q)!={'fromLocationId','fromLocationType','toLocationId','toLocationType','departureDate','tariffs'}:return False
            if q['fromLocationType']!=['CITY'] or q['toLocationType']!=['CITY'] or not numbers('fromLocationId','toLocationId'):return False
            try:return date.fromisoformat(q['departureDate'][0]).isoformat()==q['departureDate'][0]
            except ValueError:return False
        return bool(re.fullmatch(r'/restapi/routes/[1-9]\d{0,19}/simple',p.path) and set(q)=={'fromStationId','toStationId','tariffs'} and numbers('fromStationId','toStationId'))
    return False
