"""Real failure, cancellation, GUI and non-AI-search probes of owned runtime.

Only synthetic text goes to the model. The real trip table is fingerprinted,
not exported or modified. This script temporarily stops ONLY its owned service.
"""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.vacation_planner.infrastructure.local_ai.Config import LocalAIConfig,default_home
from src.vacation_planner.infrastructure.local_ai.Runtime import LocalAIRuntime,api
from src.vacation_planner.infrastructure.local_ai.LocalModelClient import LocalModelClient
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from scripts.verify_local_ai import memory_snapshot


def trips_fingerprint(store):
    with store.connect() as db:rows=db.execute('SELECT * FROM trips ORDER BY id').fetchall()
    return dict(count=len(rows),sha256=hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest())

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--live',action='store_true');parser.add_argument('--output',type=Path,default=Path('tmp/local-ai/runtime-verification'))
    args=parser.parse_args()
    if not args.live:parser.error('--live ist für tatsächliche Modell-/GUI-Prüfungen erforderlich')
    args.output.mkdir(parents=True,exist_ok=True);config=LocalAIConfig.load();runtime=LocalAIRuntime(config=config);client=LocalModelClient(config)
    if not runtime.owned():parser.error('Diese Prüfung benötigt den nachweislich selbst gestarteten Dienst. Fremde Instanzen werden nicht angehalten.')
    store=TripStore();before=trips_fingerprint(store);report=dict(cases=[],trips_before=before,model=config.model,endpoint=config.endpoint)
    def save():
        report['trips_after']=trips_fingerprint(store);report['user_trips_unchanged']=report['trips_after']==before
        (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    def expect(name,fn,error_type):
        begin=time.monotonic();item=dict(name=name)
        try:item['unexpected_result']=fn();item['passed']=False
        except error_type as exc:item.update(passed=True,error=type(exc).__name__,message=str(exc))
        except Exception as exc:item.update(passed=False,error=type(exc).__name__,message=str(exc))
        item['seconds']=time.monotonic()-begin;report['cases'].append(item);save();print(name,item['passed'],round(item['seconds'],3),flush=True)
    long_messages=[dict(role='user',content='Künstlicher Leistungstest. Schreibe alle ganzen Zahlen von 1 bis 5000 einzeln und vollständig aus, ohne Abkürzung oder Zusammenfassung.')]
    try:
        models_before=api(config.endpoint,'/api/tags')
        expect('modell_fehlt_kein_download',lambda:LocalModelClient(replace(config,model='vacation-planner-test-nichtvorhanden:local')).chat([dict(role='user',content='Künstlicher Test')]),ValueError)
        report['no_unrequested_model_download']=api(config.endpoint,'/api/tags')==models_before
        expect('echtes_ausgabelimit_wird_abgelehnt',lambda:client.chat([dict(role='user',content='Gib eine strukturierte Zusammenfassung mit einem sehr langen Text zurück.')],dict(type='object',properties=dict(summary=dict(type='string')),required=['summary'],additionalProperties=False),max_tokens=1),ValueError)
        expect('echtes_zeitlimit',lambda:client.chat(long_messages,timeout=.25,max_tokens=2048),TimeoutError)
        # Check both termination of the client and evidence of server cancellation.
        log_path=runtime.home/'server.log';offset=log_path.stat().st_size
        cancel=threading.Event();errors=[]
        def request():
            try:client.chat(long_messages,cancel=cancel,max_tokens=2048)
            except Exception as exc:errors.append(exc)
        thread=threading.Thread(target=request);thread.start();time.sleep(1.5);begin=time.monotonic();cancel.set();thread.join(2)
        report['cancellation']=dict(client_stopped=not thread.is_alive(),seconds_after_cancel=time.monotonic()-begin,error_types=[type(e).__name__ for e in errors])
        with log_path.open() as stream:stream.seek(offset);report['cancellation']['server_log_after_cancel']=stream.read()
        # A subsequent request tests whether inference kept blocking the single slot.
        begin=time.monotonic();after=client.chat([dict(role='user',content='Antworte exakt mit OK.')],max_tokens=16)
        report['cancellation']['subsequent_request_seconds']=time.monotonic()-begin;report['cancellation']['subsequent_content']=after['message']['content']
        with log_path.open() as stream:stream.seek(offset);report['cancellation']['server_log_after_cancel']=stream.read()
        # Actual GUI event loop and actual normal search, without AI app integration.
        from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
        from src.vacation_planner.core.planning.SearchRequest import SearchRequest
        app=SurprisePlannerApplication();root=app.create_window();root.withdraw()
        query=SearchRequest(countries=['EE'],interests={'Kultur':5,'Feiern':5},modes=['Zug'],regional_queries=0,price_targets=0,show_ideas=True,candidate_pool=10,shortlist=3,request_budget=4,timeout_seconds=60)
        heartbeat=[];active=True;model_result={};model_started=time.monotonic()
        def beat():
            if active:heartbeat.append(time.monotonic());root.after(20,beat)
        def model_work():
            try:model_result['response']=client.chat([dict(role='system',content='Schreibe auf Deutsch und verwende nur diese künstlichen Fakten.'),dict(role='user',content='Künstliche Prüfdaten: Drei Museen, zwei Bars, ein See ohne belegte Badestelle. Alle Preise unbekannt. Erkläre in 250 Wörtern, welche Grenzen diese Daten für Reisevorschläge haben.')],max_tokens=600)
            except Exception as exc:model_result['error']=type(exc).__name__+': '+str(exc)
            model_result['seconds']=time.monotonic()-model_started
        worker=threading.Thread(target=model_work);worker.start();beat();app.populate_request(query.to_dict());app.start_search()
        deadline=time.monotonic()+100
        while (worker.is_alive() or app.running) and time.monotonic()<deadline:root.update();time.sleep(.005)
        worker.join(.1);gaps=[b-a for a,b in zip(heartbeat,heartbeat[1:])]
        report['gui_with_model']=dict(model=model_result,heartbeat_count=len(heartbeat),max_heartbeat_gap_seconds=max(gaps,default=None),search_finished=not app.running,match_rows=len(app.tree.get_children()),idea_rows=len(app.idea_tree.get_children()),diagnostics=app.diagnostic,memory=memory_snapshot(),model_memory=api(config.endpoint,'/api/ps'))
        active=False;app.close();save()
        # Stop owned daemon, then exercise the normal GUI worker with no AI service.
        runtime.stop();expect('dienst_nicht_erreichbar',lambda:client.chat([dict(role='user',content='Künstlicher Test')]),OSError)
        report['memory_without_model']=memory_snapshot()
        app=SurprisePlannerApplication();root=app.create_window();root.withdraw();app.populate_request(query.to_dict());begin=time.monotonic();app.start_search()
        deadline=time.monotonic()+75
        while app.running and time.monotonic()<deadline:root.update();time.sleep(.005)
        report['gui_without_ai']=dict(seconds=time.monotonic()-begin,search_finished=not app.running,match_rows=len(app.tree.get_children()),idea_rows=len(app.idea_tree.get_children()),diagnostics=app.diagnostic)
        app.close();save()
    finally:
        # Leave the configured daemon available, but release model RAM if owned.
        runtime.start(lambda value:print(value,flush=True))
        if runtime.owned():api(config.endpoint,'/api/generate',dict(model=config.model,keep_alive=0),timeout=20)
        report['final_service']=dict(version=api(config.endpoint,'/api/version'),loaded=api(config.endpoint,'/api/ps'),owned=bool(runtime.owned()))
        save()
    report['passed']=all(c['passed'] for c in report['cases']) and report['no_unrequested_model_download'] and report['cancellation']['client_stopped'] and 'InterruptedError' in report['cancellation']['error_types'] and report['gui_with_model']['search_finished'] and bool(report['gui_with_model']['match_rows']+report['gui_with_model']['idea_rows']) and report['gui_without_ai']['search_finished'] and bool(report['gui_without_ai']['match_rows']+report['gui_without_ai']['idea_rows']) and report['user_trips_unchanged']
    save();print('RUNTIME REPORT',report['passed'],flush=True)
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
