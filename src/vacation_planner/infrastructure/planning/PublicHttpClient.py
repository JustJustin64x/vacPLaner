import json
import subprocess
import threading
import time
from urllib.parse import urlsplit
from .TripStore import timestamp


class PublicHttpClient:
    """No accounts/billing. Serial, cancellable curl with TLS verification, hard limits.

    curl is shipped with macOS, unlike the obsolete system Python TLS runtime.
    No retries on blocks/429; disable that source for the entire search.
    """
    _lock = threading.Lock()
    _last = {}
    USER_AGENT = 'VacationPlanner/1.0 (private local desktop; https://github.com/JustJustin64x/vacPLaner)'

    def get(self, url, context, headers=None):
        host = urlsplit(url).hostname
        if urlsplit(url).scheme != 'https' or not host:
            raise ValueError('Nur HTTPS-Datenquellen sind erlaubt.')
        if host in context.disabled:
            raise OSError(f'{host}: Quelle für diese Suche deaktiviert.')
        while not self._lock.acquire(timeout=.1):
            context.check()
        try:
            context.wait(max(0,1.1-(time.monotonic()-self._last.get(host,0))))
            context.consume()
            timeout = max(.1,min(22,context.deadline-time.monotonic()))
            extra=[]
            for key,value in (headers or {}).items():
                if key not in ('Accept','X-Currency','X-Lang') or '\n' in str(value) or '\r' in str(value):
                    raise ValueError('Nicht erlaubter öffentlicher Anfrageheader')
                extra += ['--header',key+': '+str(value)]
            process = subprocess.Popen(['curl','--silent','--show-error','--location','--max-redirs','3',
                '--proto','=https','--proto-redir','=https','--max-time',str(timeout),'--connect-timeout','8',
                '--max-filesize','8000000','--compressed','--user-agent',self.USER_AGENT,
                '--write-out','\n%{http_code}']+extra+[url],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                while True:
                    context.check()
                    try:
                        output,_ = process.communicate(timeout=.1)
                        break
                    except subprocess.TimeoutExpired:
                        continue
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
                self._last[host] = time.monotonic()
            if process.returncode:
                raise OSError(f'{host}: Netzwerkfehler oder Zeitlimit (curl {process.returncode}).')
            raw,code = output.rsplit(b'\n',1)
            if code != b'200':
                if code in (b'401',b'403',b'406',b'429'):
                    context.disabled.add(host)
                raise OSError(f'{host}: HTTP {code.decode()}; keine Sperrumgehung, Fallback wird verwendet.')
            return raw.decode('utf-8'),timestamp()
        finally:
            self._lock.release()

    def json(self, url, context, headers=None):
        body,stamp = self.get(url,context,headers=headers) if headers else self.get(url,context)
        return json.loads(body),stamp
