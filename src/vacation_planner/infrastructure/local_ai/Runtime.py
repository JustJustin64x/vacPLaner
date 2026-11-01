"""Official installation, resumable model pull and strictly owned daemon lifecycle."""
import hashlib
from contextlib import contextmanager
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import tarfile
import time
import urllib.request
from urllib.parse import urlsplit
from .Config import LocalAIConfig, default_home

RELEASE_API='https://api.github.com/repos/ollama/ollama/releases/latest'
REGISTRY='https://registry.ollama.ai/v2/library/'


def public_json(url):
    request=urllib.request.Request(url,headers={'User-Agent':'VacationPlanner-local-setup/1.0','Accept':'application/json'})
    with urllib.request.urlopen(request,timeout=25) as response:return json.load(response)


def local_opener():
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args):return None
    return urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())


def api(endpoint,path,payload=None,timeout=3):
    parsed=urlsplit(endpoint)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','::1') or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment:raise ValueError('Modell-API ausschließlich auf einer lokalen Loopback-Adresse aufrufen.')
    request=urllib.request.Request(endpoint.rstrip('/')+path,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json'})
    with local_opener().open(request,timeout=timeout) as response:return json.load(response)


class LocalAIRuntime:
    def __init__(self,home=None,config=None):
        self.home=Path(home or default_home());self.config=(config or LocalAIConfig.load(self.home)).validate()
        self.state=self.home/'service.json'

    def check_storage(self):
        repository=Path(__file__).resolve().parents[4]
        if self.home.resolve().is_relative_to(repository) or (self.home/'models').resolve().is_relative_to(repository):raise ValueError('KI-Laufzeit und Modelle müssen außerhalb des Git-Projektordners liegen.')

    @contextmanager
    def lifecycle(self):
        if platform.system()!='Darwin':raise ValueError('Dienstverwaltung ist in diesem Schritt nur auf macOS implementiert und geprüft.')
        import fcntl
        self.check_storage();self.home.mkdir(parents=True,exist_ok=True)
        with (self.home/'lifecycle.lock').open('a') as lock:
            deadline=time.monotonic()+35
            while True:
                try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);break
                except BlockingIOError:
                    if time.monotonic()>deadline:raise TimeoutError('Eine andere KI-Einrichtung verwaltet den Dienst gerade.')
                    time.sleep(.1)
            try:yield
            finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)

    def discover(self):
        paths=[shutil.which('ollama'),'/Applications/Ollama.app/Contents/Resources/ollama',str(Path.home()/'Applications/Ollama.app/Contents/Resources/ollama'),str(self.home/'runtime/bin/ollama')]
        installation=self.home/'installation.json'
        if installation.exists():paths.append(json.loads(installation.read_text()).get('binary'))
        found=[]
        for value in paths:
            if value and Path(value).is_file() and value not in found:found.append(value)
        services={}
        for endpoint in dict.fromkeys([self.config.endpoint,'http://127.0.0.1:11434']):
            try:services[endpoint]=dict(version=api(endpoint,'/api/version'),models=api(endpoint,'/api/tags'))
            except (OSError,ValueError):pass
        return dict(binaries=found,services=services,config=self.config.__dict__,home=str(self.home))

    def plan(self):
        if platform.system()!='Darwin' or platform.machine() not in ('arm64','aarch64'):raise ValueError('Automatische Laufzeiteinrichtung ist nur auf Apple-Silicon-Macs geprüft. Vorhandene Laufzeit kann separat konfiguriert werden.')
        release=public_json(RELEASE_API)
        asset=next(a for a in release['assets'] if a['name']=='ollama-darwin.tgz')
        model,tag=self.config.model.split(':',1)
        if '/' not in model:model='library/'+model
        manifest=public_json('https://registry.ollama.ai/v2/'+model+'/manifests/'+tag)
        return dict(version=release['tag_name'],release_url=release['html_url'],asset={k:asset[k] for k in ('name','size','browser_download_url','digest')},model=self.config.model,manifest=manifest,model_download_bytes=manifest['config']['size']+sum(x['size'] for x in manifest['layers']))

    def install(self,emit=print):
        self.check_storage()
        self.home.mkdir(parents=True,exist_ok=True)
        if not (self.home/'config.json').exists():self.config.save(self.home)
        discovered=self.discover()
        if discovered['binaries']:
            binary=discovered['binaries'][0];emit('Vorhandene Laufzeit wiederverwenden: '+binary);return binary
        plan=self.plan();emit(json.dumps(plan,ensure_ascii=False,indent=2))
        folder=self.home/'downloads';folder.mkdir(exist_ok=True);path=folder/('ollama-'+plan['version']+'-darwin.tgz');partial=path.with_suffix('.tgz.part')
        expected=plan['asset']['digest']
        if not expected or not expected.startswith('sha256:'):raise ValueError('Offizielle SHA-256-Prüfsumme fehlt; keine ungeprüfte Installation.')
        if not path.exists():
            command=['curl','--fail','--location','--proto','=https','--proto-redir','=https','--connect-timeout','15','--max-time','900','--continue-at','-','--output',str(partial),plan['asset']['browser_download_url']]
            emit('Offizielle Laufzeit laden; unterbrochener Download wird fortgesetzt.')
            subprocess.run(command,check=True);partial.replace(path)
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1048576),b''):digest.update(chunk)
        if 'sha256:'+digest.hexdigest()!=expected:raise ValueError('Laufzeit-Prüfsumme stimmt nicht; keine Ausführung.')
        target=self.home/'runtime';target.mkdir(exist_ok=True)
        with tarfile.open(path) as archive:
            # Data filter rejects paths escaping the target and unsafe links/devices.
            archive.extractall(target,filter='data')
        binaries=list(target.rglob('ollama'))
        binary=next((p for p in binaries if p.is_file() and os.access(p,os.X_OK)),None)
        if not binary:raise ValueError('Offizielles Archiv enthält keine ausführbare Ollama-Laufzeit.')
        (self.home/'installation.json').write_text(json.dumps(dict(**plan,binary=str(binary),archive_sha256=digest.hexdigest(),archive_bytes=path.stat().st_size),indent=2))
        return str(binary)

    def binary(self):
        installed=self.home/'installation.json'
        if installed.exists():
            path=Path(json.loads(installed.read_text())['binary'])
            if path.is_file():return str(path)
        found=self.discover()['binaries']
        if found:return found[0]
        raise ValueError('Ollama fehlt. Zuerst setup ausführen.')

    def owned(self):
        if not self.state.exists():return None
        state=json.loads(self.state.read_text())
        process=subprocess.run(['ps','-p',str(state['pid']),'-o','lstart=','-o','command='],capture_output=True,text=True)
        if process.returncode or process.stdout.strip()!=state.get('process_identity'):return None
        if state.get('endpoint')!=self.config.endpoint:return None
        return state

    def start(self,emit=print):
        with self.lifecycle():return self._start(emit)

    def _start(self,emit=print):
        try:
            version=api(self.config.endpoint,'/api/version')
            emit('Lokaler Dienst läuft bereits; keine fremde Konfiguration wird geändert.')
            return dict(version=version,owned=bool(self.owned()))
        except OSError:pass
        listeners=subprocess.run(['lsof','-nP','-iTCP:'+str(urlsplit(self.config.endpoint).port),'-sTCP:LISTEN','-t'],capture_output=True,text=True).stdout.split()
        if listeners:raise OSError('Konfigurierter Port ist belegt, aber der Dienst antwortet nicht; kein fremder Prozess wird ersetzt oder beendet.')
        self.home.mkdir(parents=True,exist_ok=True);binary=self.binary()
        environment=os.environ.copy()
        environment.update(OLLAMA_HOST=urlsplit(self.config.endpoint).netloc,OLLAMA_MODELS=str(self.home/'models'),OLLAMA_NO_CLOUD='1',OLLAMA_NUM_PARALLEL='1',OLLAMA_MAX_LOADED_MODELS='1',OLLAMA_CONTEXT_LENGTH=str(self.config.context_tokens))
        # No proxy on local transport; installation/model pull uses HTTPS separately.
        environment.pop('OLLAMA_REMOTES',None)
        log_path=self.home/'server.log'
        with log_path.open('ab') as log:process=subprocess.Popen([binary,'serve'],env=environment,stdout=log,stderr=log,start_new_session=True)
        identity=subprocess.run(['ps','-p',str(process.pid),'-o','lstart=','-o','command='],capture_output=True,text=True).stdout.strip()
        self.state.write_text(json.dumps(dict(pid=process.pid,process_identity=identity,binary=binary,endpoint=self.config.endpoint),indent=2))
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            if process.poll() is not None:raise OSError('Lokaler Dienst konnte nicht starten; siehe '+str(log_path))
            identity=subprocess.run(['ps','-p',str(process.pid),'-o','lstart=','-o','command='],capture_output=True,text=True).stdout.strip()
            try:
                version=api(self.config.endpoint,'/api/version')
                # Refuse ambiguous ownership if another listener won the port.
                listeners=subprocess.run(['lsof','-nP','-iTCP:'+str(urlsplit(self.config.endpoint).port),'-sTCP:LISTEN','-t'],capture_output=True,text=True).stdout.split()
                if str(process.pid) not in listeners:raise OSError('Port gehört einem anderen Prozess; keine Dienstzuständigkeit übernommen.')
                self.state.write_text(json.dumps(dict(pid=process.pid,process_identity=identity,binary=binary,endpoint=self.config.endpoint),indent=2))
                emit('Eigener lokaler Dienst gestartet: '+self.config.endpoint)
                return dict(version=version,owned=True)
            except (urllib.error.URLError,TimeoutError):time.sleep(.1)
        process.terminate();process.wait(timeout=5)
        self.state.unlink(missing_ok=True)
        raise TimeoutError('Lokaler Dienst ist nicht rechtzeitig bereit geworden.')

    def stop(self):
        with self.lifecycle():return self._stop()

    def _stop(self):
        state=self.owned()
        if not state:raise ValueError('Kein nachweislich selbst gestarteter Dienst; fremde Prozesse werden nicht beendet.')
        os.kill(state['pid'],signal.SIGTERM)
        for _ in range(100):
            if not self.owned():self.state.unlink(missing_ok=True);return
            time.sleep(.05)
        raise TimeoutError('Dienst hat SIGTERM noch nicht abgeschlossen; kein fremder Prozess wird beendet.')

    def pull(self,emit=print):
        existing=api(self.config.endpoint,'/api/tags')
        if any(m['name']==self.config.model for m in existing.get('models',[])):
            emit('Modell bereits vorhanden; kein erneuter Download.');return existing
        # Native Ollama pull resumes verified partial blobs. Never invoke cloud sign-in.
        request=urllib.request.Request(self.config.endpoint+'/api/pull',data=json.dumps(dict(model=self.config.model,stream=True)).encode(),headers={'Content-Type':'application/json'})
        opener=local_opener()
        last=time.monotonic()-2
        with opener.open(request,timeout=60) as response:
            for line in response:
                item=json.loads(line)
                if item.get('error'):raise OSError(item['error'])
                if time.monotonic()-last>2 or item.get('status')=='success':
                    emit(item['status']+(f" · {item.get('completed',0)/1048576:.1f}/{item['total']/1048576:.1f} MiB" if item.get('total') else ''));last=time.monotonic()
        return api(self.config.endpoint,'/api/tags')
