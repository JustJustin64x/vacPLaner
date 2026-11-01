"""Opt-in synthetic extraction and real GUI acceptance. No private text logged.

Temporarily stops only the positively owned daemon, restores it and unloads the
model. Uses public destination inventory and a disposable trip database.
"""
import argparse
import copy
from dataclasses import replace
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.vacation_planner.core.planning.TravelWishes import model_messages,model_schema,analyse_text
from src.vacation_planner.infrastructure.local_ai.WishService import WishService
from src.vacation_planner.infrastructure.local_ai.Config import LocalAIConfig
from src.vacation_planner.infrastructure.local_ai.LocalModelClient import LocalModelClient
from src.vacation_planner.infrastructure.local_ai.Runtime import LocalAIRuntime,api


class RecordingClient(LocalModelClient):
    def __init__(self,config):super().__init__(config);self.records=[]
    def chat(self,messages,schema=None,cancel=None,**kwargs):
        record=dict(messages=messages,schema=schema);self.records.append(record)
        try:
            response=super().chat(messages,schema,cancel,**kwargs);record['response']=response;return response
        except Exception as exc:
            record['error']=dict(type=type(exc).__name__,message=str(exc));raise


def triples(rows):return {(r['field'],r['value'],r['operation']) for r in rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--live',action='store_true');parser.add_argument('--resume',action='store_true');parser.add_argument('--visible',action='store_true');parser.add_argument('--output',type=Path,default=Path('tmp/local-ai-step3/live-report.json'))
    args=parser.parse_args()
    if not args.live:parser.error('--live erforderlich')
    cfg=LocalAIConfig.load();runtime=LocalAIRuntime(config=cfg)
    if not runtime.owned():parser.error('Ein nachweislich eigener laufender Dienst ist erforderlich.')
    fixture=json.loads(Path('tests/fixtures/travel_wishes/cases.json').read_text());reference=date.fromisoformat(fixture['reference_date'])
    user_path=Path(os.environ.get('VACATION_PLANNER_DB',str(Path.home()/'Library/Application Support/Urlaubsplaner/trips.sqlite3')))
    def fingerprint():
        with sqlite3.connect(user_path.as_uri()+'?mode=ro',uri=True) as db:rows=db.execute('SELECT * FROM trips ORDER BY id').fetchall()
        return dict(count=len(rows),sha256=hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    report=json.loads(args.output.read_text()) if args.resume and args.output.exists() else dict(model=cfg.model,endpoint=cfg.endpoint,cases=[],gui={})
    if report['model']!=cfg.model or report['endpoint']!=cfg.endpoint:parser.error('Konfiguration für Fortsetzung geändert.')
    report['reference_date']=str(reference);report['trips_before']=fingerprint();report['gui']={}
    tags_before=api(cfg.endpoint,'/api/tags');client=RecordingClient(cfg);service=WishService(client);app=None
    def save():args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    try:
        for case in fixture['cases']:
            if args.resume and any(c['name']==case['name'] for c in report['cases']):continue
            offset=len(client.records);begin=time.monotonic();result=None;error=None
            try:result=service.evaluate(case['text'],current_date=reference)
            except Exception as exc:error=dict(type=type(exc).__name__,message=str(exc))
            expected=triples(case['expected']);accepted=triples(result['accepted']) if result else set()
            calls=client.records[offset:]
            raw=calls[-1].get('response',{}).get('parsed',{}).get('proposals',[]) if calls else []
            item=dict(case,seconds=time.monotonic()-begin,result=result,error=error,model_calls=client.records[offset:],
                raw_reference_count=len(raw),raw_grounding_passed=result is not None and not result['rejected'],
                safety_passed=accepted<=expected,
                extraction_complete=result is not None and accepted==expected,
                omitted_expected=[dict(field=f,value=v,operation=o) for f,v,o in sorted(expected-accepted)],
                unexpected_accepted=[dict(field=f,value=v,operation=o) for f,v,o in sorted(accepted-expected)])
            report['cases'].append(item);save();print(case['name'],round(item['seconds'],3),'safety',item['safety_passed'],'complete',item['extraction_complete'],flush=True)
        # Real failure paths through new service with no central config changes.
        report['failure_probes']=[]
        for name,limited in [('ausgabelimit',replace(cfg,max_output_tokens=1)),('zeitlimit',replace(cfg,timeout_seconds=.25)),('modell_fehlt',replace(cfg,model='vacation-planner-test-nichtvorhanden:local'))]:
            c=RecordingClient(limited);begin=time.monotonic()
            try:WishService(c).evaluate('Wir sind 4 Erwachsene');item=dict(name=name,passed=False)
            except (ValueError,OSError,TimeoutError) as exc:item=dict(name=name,passed=True,error=type(exc).__name__,message=str(exc))
            item.update(seconds=time.monotonic()-begin,model_calls=c.records);report['failure_probes'].append(item)
        save()
        from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
        from src.vacation_planner.infrastructure.planning.TripStore import TripStore
        from src.vacation_planner.infrastructure.planning.DestinationInventory import DestinationInventory
        from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
        from src.vacation_planner.core.planning.SearchRequest import SearchRequest
        with tempfile.TemporaryDirectory() as directory:
            app=SurprisePlannerApplication(TripStore(Path(directory)/'trips.sqlite3'))
            app.inventory=DestinationInventory(user_path.with_name('destinations.sqlite3'));app.catalog=DestinationCatalog(app.inventory);app.provider.catalog=app.catalog
            root=app.create_window()
            if not args.visible:root.withdraw()
            panel=app.wish_panel;panel.service=service
            def input_text(text):panel.input.delete('1.0','end');panel.input.insert('1.0',text);root.update()
            def finish(seconds=100):
                until=time.monotonic()+seconds
                while panel.cancel is not None and time.monotonic()<until:root.update();time.sleep(.005)
            before=app.read_request().to_dict();text='Wir sind 4 Erwachsene; wir benötigen 2 Zimmer; Gruppenbudget: 2400 Euro'
            input_text(text);beats=[];alive=True
            def beat():
                if alive:beats.append(time.monotonic());root.after(20,beat)
            beat();offset=len(client.records);begin=time.monotonic();panel.start();finish();alive=False
            untouched=app.read_request().to_dict()==before
            rows=panel.result['accepted'] if panel.result else []
            none_preselected=not panel.selected
            ids=[r['id'] for r in rows];panel.tree.selection_set(ids);panel.toggle();panel.apply();after=app.read_request().to_dict()
            changed={k for k in before if before[k]!=after[k]}
            report['gui']['preview_and_apply']=dict(seconds=time.monotonic()-begin,preview_left_form_unchanged=untouched,
                accepted=rows,changed_fields=sorted(changed),adults=after['adults'],rooms=after['rooms'],budget=after['budget'],
                no_automatic_search=not app.running and not app.trips,none_preselected=none_preselected,heartbeat_count=len(beats),
                max_heartbeat_gap_seconds=max((b-a for a,b in zip(beats,beats[1:])),default=0),model_calls=client.records[offset:],
                passed=untouched and after['adults']==4 and after['rooms']==2 and after['budget']=='2400' and changed=={'adults','rooms','budget'} and not app.running and not app.trips)
            save()
            input_text('Im Juli 2027; 4 Erwachsene; 2 Zimmer; 7 Tage; Gruppenbudget: 2400 Euro')
            panel.start();worker=app.workers[-1];until=time.monotonic()+.7
            while time.monotonic()<until:root.update();time.sleep(.005)
            begin=time.monotonic();panel.abort()
            while worker.is_alive() and time.monotonic()-begin<4:root.update();time.sleep(.005)
            panel.poll();report['gui']['cancellation']=dict(seconds_after_cancel=time.monotonic()-begin,worker_stopped=not worker.is_alive(),no_preview=panel.result is None,form_unchanged=app.read_request().to_dict()==after)
            runtime.stop()
            offline='4 Erwachsene';input_text(offline);begin=time.monotonic();panel.start();finish(10)
            report['gui']['offline']=dict(seconds=time.monotonic()-begin,no_preview=panel.result is None,text_preserved=panel.input.get('1.0','end-1c')==offline,form_unchanged=app.read_request().to_dict()==after,message=panel.status.get())
            query=SearchRequest(countries=['EE'],interests={'Kultur':5,'Feiern':5},modes=['Zug'],regional_queries=0,price_targets=0,show_ideas=True,candidate_pool=10,shortlist=3,request_budget=4,timeout_seconds=60)
            app.populate_request(query.to_dict());begin=time.monotonic();app.start_search();until=begin+75
            while app.running and time.monotonic()<until:root.update();time.sleep(.005)
            report['gui']['manual_search_without_ai']=dict(seconds=time.monotonic()-begin,finished=not app.running,matching_rows=len(app.tree.get_children()),idea_rows=len(app.idea_tree.get_children()))
            app.close();app=None;save()
    finally:
        if app is not None and hasattr(app,'root'):app.close()
        runtime.start(lambda msg:print(msg,flush=True))
        if runtime.owned():api(cfg.endpoint,'/api/generate',dict(model=cfg.model,keep_alive=0),timeout=20)
        report['final_service']=dict(owned=bool(runtime.owned()),loaded=api(cfg.endpoint,'/api/ps'),version=api(cfg.endpoint,'/api/version'))
        report['no_model_download']=api(cfg.endpoint,'/api/tags')==tags_before;report['trips_after']=fingerprint();report['user_trips_unchanged']=report['trips_before']==report['trips_after'];save()
    g=report['gui'];report['safety_passed']=all(c['safety_passed'] for c in report['cases'])
    report['extraction_complete_count']=sum(c['extraction_complete'] for c in report['cases'])
    report['acceptance_passed']=report['safety_passed'] and all(p['passed'] for p in report['failure_probes']) and g['preview_and_apply']['passed'] and all(g['cancellation'][k] for k in ('worker_stopped','no_preview','form_unchanged')) and all(g['offline'][k] for k in ('no_preview','text_preserved','form_unchanged')) and g['manual_search_without_ai']['finished'] and g['manual_search_without_ai']['matching_rows']+g['manual_search_without_ai']['idea_rows']>0 and report['user_trips_unchanged'] and report['no_model_download']
    save();print('ACCEPTANCE',report['acceptance_passed'],'EXTRACTION',report['extraction_complete_count'],'/',len(report['cases']),flush=True)
    return 0 if report['acceptance_passed'] and report['extraction_complete_count']==len(report['cases']) else 1

if __name__=='__main__':raise SystemExit(main())
