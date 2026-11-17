"""A requested room's guests, independent of any source's tariff categories."""
from dataclasses import dataclass
from collections import Counter


@dataclass(frozen=True)
class RoomParty:
    adults: int
    children_ages: tuple = ()

    @property
    def persons(self):return self.adults+len(self.children_ages)

    def to_dict(self):return {'adults':self.adults,'children_ages':list(self.children_ages)}


def ages_from_text(text):
    if not text.strip():return []
    try:ages=[int(v.strip()) for v in text.split(',')]
    except ValueError:raise ValueError('Kinderalter bitte als ganze Jahre mit Komma trennen, zum Beispiel 4, 11.') from None
    validate_ages(ages)
    return ages


def validate_ages(ages):
    if not isinstance(ages,(list,tuple)) or len(ages)>39 or any(type(a) is not int or not 0<=a<=17 for a in ages):
        raise ValueError('Kinderalter am Reisebeginn: je Kind eine ganze Zahl von 0 bis 17.')


def room_parties(adults,children_ages,rooms,assignments=()):
    validate_ages(children_ages)
    if type(adults) is not int or type(rooms) is not int or not 1<=adults<=40 or adults+len(children_ages)>40 or not 1<=rooms<=adults+len(children_ages):
        raise ValueError('1–40 Reisende, mindestens ein Erwachsener und höchstens ein Zimmer pro Person angeben.')
    if not isinstance(assignments,(list,tuple)):raise ValueError('Zimmeraufteilung muss eine Liste sein.')
    if not assignments:
        counts=[adults//rooms+(i<adults%rooms) for i in range(rooms)]
        children=[[] for _ in range(rooms)]
        for age in children_ages:
            index=min(range(rooms),key=lambda i:counts[i]+len(children[i]))
            children[index].append(age)
        return tuple(RoomParty(n,tuple(c)) for n,c in zip(counts,children))
    if len(assignments)!=rooms:raise ValueError('Zimmeraufteilung passt nicht zur Zimmeranzahl; bitte neu verteilen.')
    result=[]
    for row in assignments:
        if isinstance(row,RoomParty):row=row.to_dict()
        if not isinstance(row,dict) or set(row)!={'adults','children_ages'}:raise ValueError('Zimmer benötigt Erwachsene und Kinderalter.')
        n=row['adults'];ages=row['children_ages'];validate_ages(ages)
        if type(n) is not int or not 0<=n<=40 or n+len(ages)<1:raise ValueError('Jedes Zimmer benötigt mindestens eine Person.')
        result.append(RoomParty(n,tuple(ages)))
    if sum(p.adults for p in result)!=adults or Counter(a for p in result for a in p.children_ages)!=Counter(children_ages):
        raise ValueError('Zimmeraufteilung muss alle Erwachsenen und jedes angegebene Kinderalter genau einmal enthalten.')
    return tuple(result)
