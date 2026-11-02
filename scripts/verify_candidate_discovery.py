"""Explicit real step-5 acceptance, public synthetic requests and temporary trips only.

Requires the existing owned daemon; no downloads. Offline checks stop only that
owned service and restore it. Run with --live; output contains public model data.
"""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.vacation_planner.infrastructure.planning.DestinationInventory import DestinationInventory
from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
from src.vacation_planner.infrastructure.planning.TripStore import TripStore,timestamp
from src.vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
from src.vacation_planner.infrastructure.planning.CandidateDiscoveryService import CandidateDiscoveryService
from src.vacation_planner.infrastructure.local_ai.Config import LocalAIConfig
from src.vacation_planner.infrastructure.local_ai.Runtime import LocalAIRuntime,api
from scripts.verify_trip_explanation import RecordingClient
from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService

PROFILES=[
 ('culture_nightlife',dict(countries=['EE'],interests={'Kultur':5,'Feiern':5})),
 ('hiking_nature_held_out',dict(countries=['SI'],interests={'Wandern':5,'Natur':5})),
 ('bathing_held_out',dict(countries=['EE'],interests={'Baden':5})),
 ('small_places_held_out',dict(countries=['EE'],target_type='kleiner Ort',interests={'Natur':4,'Kultur':2})),
 ('geographic_subregion_held_out',dict(countries=['AT'],regions=['Tirol'],interests={'Kultur':4,'Wandern':3}))]


def compact(value):
    if isinstance(value,list):return [compact(v) for v in value]
    if isinstance(value,dict):
        return {k:(dict(omitted=True,sha256=hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()) if k in ('polygons','geometry','boundary') else compact(v)) for k,v in value.items()}
    return value


def trip_summary(t,legacy):
    return dict(id=t['id'],name=t['destination']['name'],place_id=t['destination']['id'],country=t['destination']['code'],
        coordinates={k:t['destination'][k] for k in ('latitude','longitude')},type=t['destination'].get('type'),
        in_legacy_examples=any(d['code']==t['destination']['code'] and d['name']==t['destination']['name'] for d in legacy),
        filter_status=t['filter_status'],open_criteria=t['open_criteria'],score=t['score'],interest_match=t['interest_match'],
        discovery_origin=t.get('discovery_origin'),interest_evidence=t['interest_evidence'],
        source_research=t.get('source_research'),research_assessment=t.get('research_assessment'),cost_summary=t['cost_summary'],
        lodging_count=len(t['lodgings']),activity_count=len(t['activities']))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--live',action='store_true');parser.add_argument('--visible',action='store_true')
    parser.add_argument('--output',type=Path,default=Path('tmp/local-ai-step5/acceptance.json'));args=parser.parse_args()
    if not args.live:parser.error('--live erforderlich')
    cfg=LocalAIConfig.load();runtime=LocalAIRuntime(config=cfg)
    if not runtime.owned():parser.error('Bereits laufender eigener Dienst erforderlich; kein automatischer Start.')
    tags=api(cfg.endpoint,'/api/tags');client=RecordingClient(cfg)
    user_path=Path.home()/'Library/Application Support/Urlaubsplaner/trips.sqlite3'
    def fingerprint():
        with sqlite3.connect(user_path.as_uri()+'?mode=ro',uri=True) as db:rows=db.execute('SELECT * FROM trips ORDER BY id').fetchall()
        return dict(count=len(rows),sha256=hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest())
    report=dict(date='2026-11-02',model=cfg.model,trips_before=fingerprint(),profiles=[],gui={},
        comparison='Same 40 HTTP / 120 second maximum per arm, regional_queries=0, price_targets=0; normal then optional, shared warm cache within each profile, fresh temporary cache per profile. Extra research/model exposure differs; no causal quality/speed superiority claim.',
        prompt_tuning='Only the earlier EE culture/nightlife pilot was used in development. Other profiles fixed before this campaign; outputs not used to tune the prompt.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def save():args.output.write_text(json.dumps(compact(report),ensure_ascii=False,indent=2)+'\n')
    app=None
    try:
        inventory=DestinationInventory(user_path.with_name('destinations.sqlite3'));catalog=DestinationCatalog(inventory);legacy=DestinationCatalog().destinations
        report['inventory']=inventory.counts();report['representatives']=len(catalog.destinations)
        with tempfile.TemporaryDirectory() as directory:
            for index,(name,criteria) in enumerate(PROFILES):
                store=TripStore(Path(directory)/f'{index}.sqlite3');provider=OpenTravelProvider(store,catalog=catalog)
                provider.candidate_discovery=lambda cat:CandidateDiscoveryService(cat,store,client)
                q=SearchRequest(**criteria,modes=['Zug'],regional_queries=0,price_targets=0,show_ideas=True,candidate_pool=10,shortlist=3,request_budget=40,timeout_seconds=120)
                item=dict(name=name,request=q.to_dict(),runs=[]);report['profiles'].append(item)
                for enabled in (False,True):
                    ctx=SearchContext(seconds=120,budget=40);emitted={};diagnostic={};warnings=[];offset=len(client.records);begin=time.monotonic();error=None
                    def emit(k,v):
                        if k=='result':emitted[v['id']]=copy.deepcopy(v)
                        elif k=='diagnostic':diagnostic.update(v)
                        elif k in ('phase','warning'):
                            if k=='warning':warnings.append(v)
                            print(name,enabled,k,str(v)[:180],flush=True)
                    try:results=DiscoveryService(catalog,provider).search(replace(q,ai_discovery=enabled),ctx,emit)
                    except (OSError,ValueError,InterruptedError) as exc:results=list(emitted.values());error=dict(type=type(exc).__name__,message=str(exc))
                    item['runs'].append(dict(enabled=enabled,seconds=time.monotonic()-begin,http_calls=ctx.calls,error=error,warnings=warnings,
                        results=[trip_summary(t,legacy) for t in results],diagnostic=diagnostic,model_calls=client.records[offset:]))
                    save();print('COMPLETED',name,enabled,len(results),round(time.monotonic()-begin,2),flush=True)
            # Separate component controls: actual sources, not extra search results.
            from src.vacation_planner.infrastructure.planning.SourceResearchService import SourceResearchService
            from src.vacation_planner.infrastructure.planning.ResearchHttp import ResearchHttp
            from src.vacation_planner.core.planning.SourceEvidence import merge_research
            from src.vacation_planner.core.planning.ResearchAssessment import assess_research
            from src.vacation_planner.core.planning.SearchDiagnostics import SearchDiagnostics
            from urllib.parse import quote
            report['source_controls']=[]
            controls=TripStore(Path(directory)/'source-controls.sqlite3');control_provider=OpenTravelProvider(controls,catalog=catalog)
            for name in ('Bled','Innsbruck','Tallinn','Kuressaare','Leskovec'):
                ctx=SearchContext(seconds=45,budget=6);http=ResearchHttp(controls);begin=time.monotonic()
                d=catalog.resolve(name) if name in ('Bled','Innsbruck','Tallinn') else next((d for d in catalog.destinations if d['name']==name),None)
                if d is None:
                    report['source_controls'].append(dict(name=name,kind='separate_public_source_component_control',evidence=[],error=dict(type='IdentityUnresolved',message='Keine eindeutige Katalogauflösung; Kontrollabruf zurückgehalten.')))
                    save();continue
                d=copy.deepcopy(d);d['wikivoyage_source']=d.get('wikivoyage_source') or 'https://de.wikivoyage.org/wiki/'+quote(name.replace(' ','_'),safe='')
                entry=dict(name=name,kind='separate_public_source_component_control',evidence=[])
                q=SearchRequest(interests={'Kultur':5},ai_discovery=True,modes=['Zug'],price_targets=0,regional_queries=0)
                try:
                    rows,gaps=SourceResearchService(controls,http).collect(dict(destination=d,request=q.to_dict()),ctx,lambda *a:None)
                    entry.update(evidence=rows,gaps=gaps)
                    # Source acceptance is independent of model suggestions. The
                    # ordinary planner may already know the same facilities.
                    planner=DiscoveryService(catalog,control_provider);planner.diagnostics=SearchDiagnostics(q)
                    travel_context=SearchContext(seconds=35,budget=6);travel_context.request=q
                    trip=planner.research(q,travel_context,dict(latitude=52.52,longitude=13.405,name='Berlin'),d,lambda *a:None)
                    if trip:
                        costs=copy.deepcopy(trip['cost_summary']);score=trip['score']
                        trip=merge_research(trip,rows,dict(status='source_observations',attempted_at=timestamp()))
                        assess_research(trip,q)
                        entry.update(assessment=trip['research_assessment'],score_before=score,score_after=trip['score'],costs_unchanged=costs==trip['cost_summary'])
                    entry['ordinary_component_http_calls']=travel_context.calls
                except (OSError,ValueError,KeyError,InterruptedError) as exc:entry['error']=dict(type=type(exc).__name__,message=str(exc))
                entry.update(seconds=time.monotonic()-begin,calls=ctx.calls,audit=http.audit)
                report['source_controls'].append(entry);save();print('SOURCE CONTROL',name,len(entry['evidence']),entry.get('error'),flush=True)
            from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
            store=TripStore(Path(directory)/'gui.sqlite3');provider=OpenTravelProvider(store,catalog=catalog)
            provider.candidate_discovery=lambda cat:CandidateDiscoveryService(cat,store,client)
            app=SurprisePlannerApplication(store,provider);app.inventory=inventory;app.catalog=catalog;provider.catalog=catalog
            root=app.create_window()
            if not args.visible:root.withdraw()
            q=SearchRequest(countries=['EE'],interests={'Kultur':5,'Feiern':5},modes=['Zug'],regional_queries=0,price_targets=0,show_ideas=True,candidate_pool=10,shortlist=3,request_budget=40,timeout_seconds=120)
            def gui_run(label,request):
                app.populate_request(request.to_dict());beats=[];alive=True
                def beat():
                    if alive:beats.append(time.monotonic());root.after(20,beat)
                beat();begin=time.monotonic();app.start_search();worker=app.workers[-1]
                while worker.is_alive() and time.monotonic()-begin<135:root.update();time.sleep(.005)
                app.poll();alive=False
                if worker.is_alive():app.cancel_search();worker.join(5)
                if app.active:app.show_details()
                entry=dict(seconds=time.monotonic()-begin,finished=not worker.is_alive(),heartbeat_count=len(beats),
                    max_heartbeat_gap_seconds=max((b-a for a,b in zip(beats,beats[1:])),default=0),
                    results=[trip_summary(t,legacy) for t in app.trips.values()],diagnostic=app.diagnostic,
                    details_contain_origin='Zusätzliche KI-Idee' in app.details.get('1.0','end'))
                report['gui'][label]=entry;save();print('GUI',label,entry['finished'],len(app.trips),flush=True)
            gui_run('with_ai',replace(q,ai_discovery=True))
            extras=[t for t in app.trips.values() if t.get('discovery_origin')]
            if extras:
                extra=extras[0];saved=store.save('Explicit acceptance snapshot',extra);loaded=store.load(saved)
                report['gui']['explicit_save_preserves_origin']=loaded['discovery_origin']==extra['discovery_origin'] and loaded.get('source_research')==extra.get('source_research')
                app.tree.selection_set(extra['id']);app.select_trip();app.show_details()
                report['gui']['additional_details_visible']='Zusätzliche KI-Idee' in app.details.get('1.0','end')
            # Actual GUI cancellation, tokens validated further by reproducible desktop tests.
            app.populate_request(replace(q,ai_discovery=True).to_dict());app.start_search();worker=app.workers[-1]
            until=time.monotonic()+.5
            while time.monotonic()<until:root.update();time.sleep(.005)
            begin=time.monotonic();app.cancel_search()
            while worker.is_alive() and time.monotonic()-begin<5:root.update();time.sleep(.005)
            app.poll();report['gui']['cancel']=dict(seconds=time.monotonic()-begin,worker_stopped=not worker.is_alive())
            runtime.stop()
            gui_run('normal_without_service',q)
            gui_run('optional_without_service',replace(q,ai_discovery=True))
            app.close();app=None
    finally:
        if app is not None:app.close()
        runtime.start(lambda value:print(value,flush=True))
        if runtime.owned():api(cfg.endpoint,'/api/generate',dict(model=cfg.model,keep_alive=0),timeout=20)
        report['user_trips_unchanged']=fingerprint()==report['trips_before'];report['no_model_download']=api(cfg.endpoint,'/api/tags')==tags
        report['final_service']=dict(owned=bool(runtime.owned()),loaded=api(cfg.endpoint,'/api/ps'));save()
    report['checks']=dict(five_profiles=len(report['profiles'])==5,
        additional_nonlegacy_match=any(t.get('discovery_origin') and not t['in_legacy_examples'] and t['filter_status']=='passend' for p in report['profiles'] for r in p['runs'] for t in r['results']),
        bounded_calls=all(r['http_calls']<=40 and len(r['model_calls'])<=int(r['enabled']) for p in report['profiles'] for r in p['runs']),
        gui_finished=all(report['gui'][k]['finished'] and report['gui'][k]['results'] for k in ('with_ai','normal_without_service','optional_without_service')),
        cancel=report['gui']['cancel']['worker_stopped'],saved=report['gui'].get('explicit_save_preserves_origin',False),
        preserved=report['user_trips_unchanged'] and report['no_model_download'])
    report['passed']=all(report['checks'].values());save();print('FINAL',report['passed'],report['checks'],flush=True)
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
