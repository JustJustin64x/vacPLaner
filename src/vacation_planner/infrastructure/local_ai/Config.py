"""Portable, explicit local-only configuration. No runtime is started on import."""
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

DEFAULT_MODEL='qwen3:4b-instruct-2507-q4_K_M'

def default_home():
    if os.environ.get('VACATION_PLANNER_AI_HOME'):return Path(os.environ['VACATION_PLANNER_AI_HOME']).expanduser()
    if sys.platform=='darwin':return Path.home()/'Library/Application Support/Urlaubsplaner/local-ai'
    if sys.platform=='win32':return Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData/Local'))/'Urlaubsplaner/local-ai'
    return Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))/'urlaubsplaner/local-ai'

@dataclass(frozen=True)
class LocalAIConfig:
    model:str=DEFAULT_MODEL
    endpoint:str='http://127.0.0.1:11435'
    timeout_seconds:float=90
    context_tokens:int=4096
    max_output_tokens:int=768
    parallel_requests:int=1
    keep_alive:str='5m'

    def validate(self):
        if not isinstance(self.endpoint,str) or not isinstance(self.model,str):raise ValueError('Modell und Endpunkt müssen Text sein.')
        if type(self.context_tokens) is not int or type(self.max_output_tokens) is not int or type(self.timeout_seconds) not in (int,float):raise ValueError('Ungültige numerische KI-Konfiguration.')
        parsed=urlsplit(self.endpoint)
        if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','::1') or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment:raise ValueError('KI-Endpunkt muss eine lokale Loopback-HTTP-Adresse ohne Pfad sein.')
        if not parsed.port:raise ValueError('Lokalen Port ausdrücklich angeben.')
        if not re.fullmatch(r'[A-Za-z0-9_./-]+:[A-Za-z0-9_.-]+',self.model) or any(x in self.model.lower() for x in ('cloud','http','..')):raise ValueError('Nur ausdrücklich benannte lokale Modell-Tags sind erlaubt.')
        if self.parallel_requests!=1:raise ValueError('Für diese Einrichtung ist genau eine gleichzeitige Modellaufgabe erlaubt.')
        if not 256<=self.context_tokens<=8192 or not 1<=self.max_output_tokens<=4096 or not .01<=self.timeout_seconds<=600:raise ValueError('Ungültige Kontext-, Ausgabe- oder Zeitbegrenzung.')
        if not re.fullmatch(r'(0|[1-9][0-9]*[smh])',self.keep_alive):raise ValueError('Ungültige Modell-Haltezeit.')
        return self

    @classmethod
    def load(cls,home=None):
        path=Path(home or default_home())/'config.json'
        if not path.exists():return cls().validate()
        try:return cls(**json.loads(path.read_text())).validate()
        except TypeError as exc:raise ValueError('KI-Konfiguration enthält unbekannte Felder oder falsche Datentypen.') from exc

    def save(self,home=None):
        self.validate();home=Path(home or default_home());home.mkdir(parents=True,exist_ok=True)
        path=home/'config.json'
        if path.exists():raise FileExistsError('Vorhandene KI-Konfiguration wird nicht überschrieben.')
        path.write_text(json.dumps(asdict(self),ensure_ascii=False,indent=2)+'\n');return path
