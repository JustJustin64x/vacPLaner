"""Bounded spatial retrieval, shared with the existing discovery pipeline."""
import copy
from ..domain.value_objects.GeographicCoordinates import GeographicCoordinates


def distance(a,b):
    return GeographicCoordinates(a['latitude'],a['longitude']).calculate_distance_in_kilometers_to(
        GeographicCoordinates(b['latitude'],b['longitude']))


def deduplicate(items):
    result=[]
    for item in items:
        duplicate=False
        for old in result:
            same_id=item.get('id') and item.get('id')==old.get('id')
            located=all(x.get(k) is not None for x in (item,old) for k in ('latitude','longitude'))
            same_place=located and item['name'].casefold()==old['name'].casefold() and distance(item,old)<.1
            if same_id or same_place:
                duplicate=True;break
        if not duplicate:result.append(item)
    return result


class PlaceResearch:
    def __init__(self,catalog,provider):self.catalog,self.provider=catalog,provider

    def collect(self,base,request,context,emit):
        result=dict(lodgings=[],activities=[],warnings=[],cache_note='',sources=[])
        pages=[base]
        if request.surroundings:pages+=self.catalog.nearby(base,request)
        for index,page in enumerate(pages):
            context.check()
            if index and sum(l['type'] in request.accommodation_types and all(l.get('amenities',{}).get(k) is True for k in request.required) for l in result['lodgings'])>=2 and (not any(request.interests.values()) or any(
                    any(request.interests.get(t,0)>0 for t in a['topics']) for a in result['activities'])):break
            if index:emit('phase',base['name']+' – Unterkünfte und Aktivitäten im erlaubten Umkreis: '+page['name'])
            try:
                data=self.provider.places(page,context)
            except InterruptedError:raise
            except (OSError,ValueError) as exc:
                result['warnings'].append('Quelle fehlgeschlagen: '+str(exc));continue
            if index==0 and request.surroundings and len(data.get('lodgings',[]))<2:
                # Only source-linked child pages of this very article, no recursion.
                related=[dict(base,**p) for p in data.get('related_pages',[])]
                pages[:]=[base]+(related+pages[1:])[:2]
            result['warnings']+=data.get('warnings',[])
            result['sources'].append(dict(source=page['source'],note=data.get('cache_note','')))
            result['cache_note']+=' '+page['name']+': '+data.get('cache_note','')
            for kind,radius in [('lodgings',float(request.lodging_radius_km)),('activities',float(request.activity_radius_km))]:
                for raw in data.get(kind,[]):
                    item=copy.deepcopy(raw)
                    located=all(item.get(k) is not None for k in ('latitude','longitude'))
                    separation=distance(base,item) if located else None
                    # Outside pages require coordinates. Unknown local locations remain explicit.
                    if (index or request.countries or request.regions or request.excluded) and not located:continue
                    if located and separation>(radius if request.surroundings else min(2,radius)):continue
                    if located:
                        nearest=min(self.catalog.destinations,key=lambda d:distance(item,d))
                        if not self.catalog.allowed(nearest,request):continue
                    item.update(distance_km=separation,source_place=page.get('base_name',page['name']),source_page_name=page['name'],
                                location_name=item.get('address') or page['name'],
                                vicinity=bool(index or (separation is not None and separation>2)),
                                distance_kind='Luftlinie; Erreichbarkeit nicht belegt')
                    result[kind].append(item)
                result[kind]=deduplicate(result[kind])
        return result
