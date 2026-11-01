"""Versioned geographic policy; source country codes remain GeoNames' attribution.

EEA's Ural/Manych/Bosporus convention, with explicit island exceptions.
The eastern line is a documented coarse polyline, not an administrative border.
"""
VERSION='europe-eea-v1'
EXTRA_COUNTRIES={'BY':'Belarus','RU':'Russland (europäischer Teil)','TR':'Türkei (europäischer Teil)',
 'KZ':'Kasachstan (westlich des Ural)','GI':'Gibraltar','GG':'Guernsey','JE':'Jersey','IM':'Isle of Man','SJ':'Spitzbergen und Jan Mayen'}
EXCLUDED={'AM':'Armenien','AZ':'Aserbaidschan','GE':'Georgien','GL':'Grönland'}
# lon, lat: west of the Urals, north of the Manych depression.
EASTERN_RING=[(-30,46),(38,46),(42,46.3),(45,45.7),(48,45.5),(51.5,47),
 (51.3,49),(51.4,51),(55,51.8),(58.5,54.5),(59.5,58),(59,61),
 (61,64),(65,67),(67,70),(70,77),(70,83),(-30,83)]
THRACE=[(25.5,39.5),(26.1,40.0),(26.7,40.4),(27.5,40.8),(28.98,41.0),
 (29.08,41.05),(29.03,41.17),(29.14,41.24),(29.3,42.2),(25.5,42.2)]

def in_ring(lat,lon,ring):
    inside=False
    for a,b in zip(ring,ring[1:]+ring[:1]):
        if (a[1]>lat)!=(b[1]>lat) and lon<(b[0]-a[0])*(lat-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside

def contains(code,lat,lon):
    if code in EXCLUDED:return False
    if code in ('RU','KZ'):return in_ring(lat,lon,EASTERN_RING)
    if code=='TR':return in_ring(lat,lon,THRACE) or (39.7<=lat<=40.3 and 25.5<=lon<=26.1) # Imbros/Tenedos
    if code=='FR':return 41<=lat<=51.2 and -5.5<=lon<=10 # metropolitan incl. Corsica
    if code=='ES':return 35.95<=lat<=44 and -10<=lon<=4.5 # excludes Canaries/Ceuta/Melilla
    if code=='PT':return 30<=lat<=42.3 and -32<=lon<=-6 # explicit Azores/Madeira exception
    if code=='NO':return 57<=lat<=72 and -10<=lon<=33
    if code=='DK':return 54<=lat<=58 and 7<=lon<=16
    if code=='NL':return 50<=lat<=54 and 3<=lon<=8
    if code=='GB':return 49<=lat<=61.5 and -9<=lon<=2.5
    if code=='SJ':return 70<=lat<=82 and -10<=lon<=37
    if code=='CY':return 34<=lat<=36 and 32<=lon<=35 # explicit Mediterranean exception
    return 34<=lat<=72 and -25<=lon<=46
