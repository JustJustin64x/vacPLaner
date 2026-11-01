"""Small explicit JSON-schema subset used by the offline probes.

Not a general JSON Schema engine. Model grammar and this validator do not prove
factual truth; semantic assertions are evaluated separately in the live probes.
"""
import math


def validate_json(value,schema,path='$'):
    allowed={'type','properties','required','additionalProperties','items','enum','minimum','maximum','minItems','maxItems','description','title'}
    unknown=set(schema)-allowed
    if unknown:raise ValueError('Nicht unterstützte Schema-Regeln: '+', '.join(sorted(unknown)))
    types=schema.get('type');types=[types] if isinstance(types,str) else types or []
    matches={'null':value is None,'boolean':type(value) is bool,'integer':type(value) is int,'number':type(value) in (int,float) and math.isfinite(value),'string':isinstance(value,str),'array':isinstance(value,list),'object':isinstance(value,dict)}
    if types and not any(matches.get(t,False) for t in types):raise ValueError(path+': falscher Datentyp')
    if 'enum' in schema and not any(type(value) is type(item) and value==item for item in schema['enum']):raise ValueError(path+': Wert außerhalb enum')
    if isinstance(value,dict):
        missing=set(schema.get('required',[]))-set(value)
        if missing:raise ValueError(path+': Pflichtfelder fehlen: '+', '.join(sorted(missing)))
        props=schema.get('properties',{})
        if schema.get('additionalProperties') is False and set(value)-set(props):raise ValueError(path+': zusätzliche Felder nicht erlaubt')
        for key,item in value.items():
            if key in props:validate_json(item,props[key],path+'.'+key)
    elif isinstance(value,list):
        if len(value)<schema.get('minItems',0) or len(value)>schema.get('maxItems',float('inf')):raise ValueError(path+': falsche Listenlänge')
        if 'items' in schema:
            for index,item in enumerate(value):validate_json(item,schema['items'],path+'['+str(index)+']')
    elif type(value) in (int,float):
        if not math.isfinite(value) or value<schema.get('minimum',float('-inf')) or value>schema.get('maximum',float('inf')):raise ValueError(path+': Zahl außerhalb des Bereichs')
    return value
