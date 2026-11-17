"""Bounded per-unit allocation; alternative tariffs never create extra stock."""
from dataclasses import dataclass
from ...core.planning.RoomParty import RoomParty


@dataclass(frozen=True)
class Beds24RoomSelection:
    room_id: str
    offer_id: str
    parties: tuple

    @property
    def quantity(self):return len(self.parties)

    @property
    def adults(self):return sum(p.adults for p in self.parties)


def selections(rooms,parties,limit=4,check=lambda:None):
    found=[];seen=set();visited=0
    def walk(index,chosen):
        nonlocal visited
        check();visited+=1
        if visited>2048 or len(found)>=limit:return
        if index==len(parties):
            signature=tuple(sorted((rid,offer,tuple(sorted((p.adults,tuple(sorted(p.children_ages))) for p in people))) for rid,(offer,people) in chosen.items()))
            if signature not in seen:
                seen.add(signature);found.append(tuple(Beds24RoomSelection(rid,offer,tuple(people)) for rid,(offer,people) in chosen.items()))
            return
        party=parties[index]
        for room in rooms[:24]:
            rid=room['rid'];offer=room['offer'];old=chosen.get(rid)
            if old and old[0]!=offer:continue
            people=old[1] if old else ();quantity=len(people)+1
            if quantity not in room['quantities']:continue
            options=room.get('unit_options',{}).get(quantity)
            if options is None:continue
            if party.adults not in options['adults'] or len(party.children_ages) not in options['children']:continue
            chosen[rid]=(offer,people+(party,));walk(index+1,chosen)
            if old:chosen[rid]=old
            else:chosen.pop(rid,None)
    walk(0,{});return found


def selection_rows(choice,rooms=()):
    if not isinstance(choice,dict):return tuple(choice)
    return tuple(Beds24RoomSelection(rid,next((r['offer'] for r in rooms if r['rid']==rid),'1'),tuple(RoomParty(adults) for _ in range(quantity))) for rid,(quantity,adults) in choice.items())
