"""Canonical source observations, never model-authored facts or ranking input."""
import copy
import hashlib
import json

KINDS=('listing','published_hours','access_note')
LIMITATION=('Aussage der Quelle, nicht unabhängig bestätigt. Keine Zusage für den Reisetag, '
            'sichere Bade-/Wandereignung, Ruhe, gemeinsame Öffnung, Fußweg, Preis oder Buchbarkeit. '
            'Fehlende Daten belegen kein fehlendes Angebot.')


def evidence_id(value):
    return 'sr-'+hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:24]


def selection_schema():
    return dict(type='object',properties=dict(selected=dict(type='array',maxItems=6,items=dict(type='object',
        properties=dict(id=dict(type='string',description='Exakte vorgegebene Beleg-ID.'),kind=dict(type='string',enum=list(KINDS))),
        required=['id','kind'],additionalProperties=False))),required=['selected'],additionalProperties=False)


def validate_selection(value,evidence):
    if not isinstance(value,dict) or set(value)!={'selected'} or not isinstance(value['selected'],list) or len(value['selected'])>6:raise ValueError('Ungültige Quellenauswahl.')
    known={e['id']:e for e in evidence};seen=set()
    for row in value['selected']:
        if not isinstance(row,dict) or set(row)!={'id','kind'} or not isinstance(row['id'],str) or row['id'] not in known or row['id'] in seen or row['kind']!=known[row['id']]['kind']:
            raise ValueError('Fremde, doppelte oder falsch interpretierte Quellenreferenz.')
        seen.add(row['id'])
    return seen


def merge_research(trip,evidence,attempt):
    """Bounded history. Never overwrite an older different source assertion."""
    result=copy.deepcopy(trip)
    research=result.setdefault('source_research',dict(version=1,evidence=[],attempts=[]))
    known={e['id']:e for e in research['evidence']}
    added=0
    for e in evidence:
        if e['id'] in known:
            # Keep original provenance; latest use is explicitly separate.
            known[e['id']]['last_used_at']=attempt['attempted_at']
            known[e['id']]['last_use_from_cache']=e.get('cache_used',False)
            known[e['id']]['model_selected']=e.get('model_selected',False)
            if not e.get('cache_used'):known[e['id']]['last_seen_at']=e['retrieved_at']
            continue
        if len(research['evidence'])>=64:
            attempt['history_limit_reached']=True;continue
        row=copy.deepcopy(e);research['evidence'].append(row);known[row['id']]=row;added+=1
    groups={}
    for e in research['evidence']:
        if e['kind']=='listing':continue
        key=(e['subject']['id'],e['kind']);groups.setdefault(key,[]).append(e)
    for rows in groups.values():
        if len({r['quote'] for r in rows})>1:
            for row in rows:row['conflict']='Abweichende Quellenaussagen/zeitliche Änderungen; nicht automatisch aufgelöst.'
    attempt=dict(attempt,added=added)
    research['attempts']=(research.get('attempts',[])+[attempt])[-8:]
    return result


def sections(trip):
    research=trip.get('source_research')
    if not research:return []
    latest=(research.get('attempts') or [{}])[-1]
    status={'failed':'fehlgeschlagen','limited':'Budget oder Zeitlimit erreicht','source_observations':'Quellenhinweise vorhanden','no_usable_observations':'keine ausreichend belegten Hinweise'}.get(latest.get('status'),'Status offen')
    paragraphs=['Gezielte Wikivoyage-/Wikidata-Recherche. Neue Quellenhinweise sind separat und ohne Rankingwirkung. Die Passungserklärung nutzt weiterhin ihre bisherigen Interessenbelege.',
        'Letzter Versuch: '+latest.get('attempted_at','unbekannt')+' · '+status+' · '+latest.get('message',''),
        'Lokale KI: '+latest.get('model_status','nicht ausgeführt')+'. Keine neue unabhängige Bestätigung durch das Modell.']
    paragraphs+=latest.get('gaps',[])
    if latest.get('history_limit_reached'):paragraphs.append('Beleggrenze der Arbeitskopie erreicht; ältere Belege erhalten, zusätzliche Hinweise nicht aufgenommen.')
    result=[('Neue Quellenhinweise · Grenzen und Rechercheverlauf',paragraphs,[('Wikivoyage · Lizenz und Herkunft','https://de.wikivoyage.org/wiki/Wikivoyage:Lizenzbestimmungen')])]
    names={'listing':'Strukturierter Quelleneintrag','published_hours':'Veröffentlichte Öffnungs-/Saisonangabe','access_note':'Zugangshinweis der Quelle'}
    for e in research.get('evidence',[]):
        lines=['Quelle: '+e['source']+' · '+e.get('licensing','Lizenz siehe Quelle'),
            'Art: '+names[e['kind']]+' · Status: '+e['verification_status'],
            ('KI-Auswahl dieses Hinweises: ja; keine unabhängige Faktenbestätigung.' if e.get('model_selected') else 'Deterministischer Quellenhinweis; nicht durch KI ausgewählt.'),
            'Originalnachweis: „'+e['quote']+'“',
            'Quelle abgerufen: '+e['retrieved_at']+(' · extrahierter Cache, keine neue Liveprüfung' if e.get('last_use_from_cache',e.get('cache_used')) else ''),
            'Veröffentlichung/Gültigkeit: '+(e.get('publication_at') or 'unbekannt')+' · Quellenpflege: '+(e.get('source_update_note') or 'unbekannt'),
            e['limitations']]
        if e.get('conflict'):lines.append(e['conflict'])
        lines.append('Zielzuordnung: '+e['identity']['method']+'; Institution/Kartenpunkt im gewählten Umkreis. Kein bestätigter Zugang.')
        result.append((e['subject']['name']+' · '+names[e['kind']],lines,[('Quelleneintrag',e['source_url']),('Ortsidentität / Wikidata',e['identity']['wikidata_url'])]))
    return result
