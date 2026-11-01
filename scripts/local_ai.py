"""Explicit optional local AI setup. Does not change or start the travel search."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.vacation_planner.infrastructure.local_ai.Runtime import LocalAIRuntime,api


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['plan','setup','start','stop','status','check'])
    parser.add_argument('--download',action='store_true',help='Ausdrückliche Auswahl: offizielle Laufzeit / ausgewähltes Modell herunterladen')
    parser.add_argument('--home',type=Path,help='Optionales separates KI-Datenverzeichnis')
    args=parser.parse_args();runtime=LocalAIRuntime(args.home)
    def emit(value):print(value,flush=True)
    try:
        if args.command=='plan':emit(json.dumps(runtime.plan(),ensure_ascii=False,indent=2))
        elif args.command=='status':emit(json.dumps(runtime.discover(),ensure_ascii=False,indent=2))
        elif args.command=='setup':
            if not runtime.discover()['binaries'] and not args.download:
                emit(json.dumps(runtime.plan(),ensure_ascii=False,indent=2));emit('Für den angekündigten Download setup --download verwenden.');return 2
            runtime.install(emit);runtime.start(emit)
            if not any(m['name']==runtime.config.model for m in api(runtime.config.endpoint,'/api/tags').get('models',[])):
                emit(json.dumps(runtime.plan(),ensure_ascii=False,indent=2))
                if not args.download:emit('Für den angekündigten Modelldownload setup --download verwenden.');return 2
            emit(json.dumps(runtime.pull(emit),ensure_ascii=False,indent=2))
        elif args.command=='start':emit(json.dumps(runtime.start(emit),ensure_ascii=False,indent=2))
        elif args.command=='stop':runtime.stop();emit('Eigener lokaler Dienst beendet.')
        elif args.command=='check':
            from src.vacation_planner.infrastructure.local_ai.LocalModelClient import LocalModelClient
            result=LocalModelClient(runtime.config).chat([dict(role='user',content='Antworte kurz auf Deutsch: Ist diese Antwort lokal erzeugt?')]);emit(json.dumps(result,ensure_ascii=False,indent=2))
    except (OSError,ValueError,TimeoutError,KeyboardInterrupt) as exc:
        emit('Einrichtung/Prüfung beendet: '+str(exc));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
