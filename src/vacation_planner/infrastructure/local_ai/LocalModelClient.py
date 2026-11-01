"""Optional bounded local transport, independent of the travel provider.

Cancelling kills this client's curl process and closes the HTTP connection.
It does not stop a daemon or unload a model used by somebody else. Whether
server inference has stopped must be observed separately, not assumed.
"""
import json
import subprocess
import threading
import time
import urllib.error
from .Config import LocalAIConfig
from .Runtime import api
from .Validation import validate_json


class LocalModelClient:
    _locks={}
    _guard=threading.Lock()

    def __init__(self,config=None):
        self.config=(config or LocalAIConfig.load()).validate()
        with self._guard:self.lock=self._locks.setdefault(self.config.endpoint,threading.Lock())

    def require_local_model(self,timeout=None):
        try:show=api(self.config.endpoint,'/api/show',dict(model=self.config.model),timeout=min(3,self.config.timeout_seconds if timeout is None else timeout))
        except urllib.error.HTTPError as exc:
            if exc.code==404:raise ValueError('Lokales Modell fehlt: '+self.config.model) from None
            raise OSError('Lokaler Modelldienst: HTTP '+str(exc.code)) from None
        except TimeoutError:raise TimeoutError('Zeitlimit bei der lokalen Modellprüfung erreicht.') from None
        except OSError as exc:raise OSError('Lokaler KI-Dienst nicht erreichbar: '+self.config.endpoint) from exc
        if show.get('remote_host') or show.get('remote_model') or show.get('details',{}).get('format')!='gguf':raise ValueError('Modell ist nicht als lokale GGUF-Datei nachgewiesen; kein Cloud-Fallback.')
        return show

    def chat(self,messages,schema=None,cancel=None,timeout=None,max_tokens=None,keep_alive=None):
        cancel=cancel or threading.Event();limit=self.config.timeout_seconds if timeout is None else min(timeout,self.config.timeout_seconds)
        if limit<=0:raise ValueError('Zeitlimit muss positiv sein.')
        start=time.monotonic();deadline=start+limit
        def check():
            if cancel.is_set():raise InterruptedError('Lokale KI-Anfrage abgebrochen; Verbindung geschlossen. Dienst bleibt erhalten.')
            if time.monotonic()>=deadline:raise TimeoutError('Zeitlimit der lokalen KI-Anfrage erreicht; Verbindung geschlossen.')
        check()
        if not isinstance(messages,list) or not messages:raise ValueError('Nachrichten fehlen.')
        if any(not isinstance(m,dict) or m.get('role') not in ('system','user','assistant') or not isinstance(m.get('content'),str) or set(m)-{'role','content'} for m in messages):raise ValueError('Nur begrenzte Textnachrichten sind erlaubt; keine Tools oder Bilddaten.')
        if sum(len(m['content']) for m in messages)+len(json.dumps(schema or {}))>min(12000,self.config.context_tokens*2):raise ValueError('Eingabe überschreitet das konservative Kontextlimit; Text vorher gezielt kürzen.')
        if schema is not None:
            # Ollama's format constrains grammar; the model also needs the actual
            # contract in its context to interpret field meanings correctly.
            messages=[dict(m) for m in messages]
            contract='\nAusgabevertrag (JSON-Schema):\n'+json.dumps(schema,ensure_ascii=False)
            if messages[0]['role']=='system':messages[0]['content']+=contract
            else:messages.insert(0,dict(role='system',content=contract))
        tokens=self.config.max_output_tokens if max_tokens is None else max_tokens
        if type(tokens) is not int or not 1<=tokens<=4096:raise ValueError('Ungültiges Ausgabelimit.')
        while not self.lock.acquire(timeout=min(.05,max(.001,deadline-time.monotonic()))):check()
        process=None
        try:
            check();show=self.require_local_model(timeout=max(.001,deadline-time.monotonic()));check()
            request=dict(model=self.config.model,messages=messages,stream=False,options=dict(num_ctx=self.config.context_tokens,num_predict=tokens,temperature=0,seed=42),keep_alive=keep_alive or self.config.keep_alive)
            if 'thinking' in show.get('capabilities',[]):request['think']=False
            if schema is not None:request['format']=schema
            payload=json.dumps(request,ensure_ascii=False).encode()
            process=subprocess.Popen(['curl','--silent','--show-error','--noproxy','*','--connect-timeout','2','--max-time',str(max(.01,deadline-time.monotonic())),
                '--max-filesize','2000000','--header','Content-Type: application/json','--data-binary','@-','--write-out','\n%{http_code}',self.config.endpoint+'/api/chat'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            first=True
            while True:
                check()
                try:
                    raw,err=process.communicate(input=payload if first else None,timeout=.05);break
                except subprocess.TimeoutExpired:first=False
            check()
            if process.returncode:
                if process.returncode==28:raise TimeoutError('Zeitlimit der lokalen KI-Verbindung erreicht.')
                raise OSError('Lokale KI-Verbindung fehlgeschlagen (curl '+str(process.returncode)+').')
            body,code=raw.rsplit(b'\n',1)
            if code!=b'200':
                if code==b'404':raise ValueError('Lokales Modell oder Endpunkt nicht vorhanden.')
                raise OSError('Lokaler KI-Dienst: HTTP '+code.decode())
            try:response=json.loads(body)
            except (ValueError,UnicodeError):raise ValueError('Ungültige JSON-Antwort des lokalen Dienstes.') from None
            if response.get('error'):raise ValueError('Lokale Modellantwort meldet einen Fehler: '+str(response['error']))
            if not response.get('done') or response.get('done_reason')=='length':raise ValueError('Lokale Antwort unvollständig oder am Ausgabelimit abgeschnitten.')
            content=response.get('message',{}).get('content')
            if not isinstance(content,str) or not content.strip():raise ValueError('Lokale Modellantwort enthält keinen Text.')
            if schema is not None:
                try:parsed=json.loads(content)
                except ValueError:raise ValueError('Modell lieferte keine gültige strukturierte Antwort.') from None
                response['parsed']=validate_json(parsed,schema)
            response['client_seconds']=time.monotonic()-start
            return response
        finally:
            if process and process.poll() is None:process.kill();process.communicate()
            self.lock.release()
