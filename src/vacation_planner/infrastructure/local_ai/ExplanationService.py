"""Optional local explanation, no lifecycle/start/download operations."""
import copy
from collections import OrderedDict
import threading
from ...core.planning.TripExplanation import (
    VERSION, build_context, contract, digest, fit_context, messages, render, validate_selection,
)
from .Config import LocalAIConfig
from .LocalModelClient import LocalModelClient

START_HINT = 'Lokalen Dienst im Projekt starten: .venv/bin/python scripts/local_ai.py start'


class ExplanationService:
    def __init__(self, client=None):
        self.client = client  # Lazy config load: malformed AI config cannot break app/search.
        self.cache = OrderedDict()
        self.guard = threading.Lock()

    @staticmethod
    def key(trip):
        # Local digest only; no private request/history is transmitted or persisted.
        return digest([VERSION, trip])

    def explain(self, trip, cancel=None):
        cancel = cancel or threading.Event()
        if cancel.is_set():
            raise InterruptedError('Erklärung abgebrochen.')
        key = self.key(trip)
        with self.guard:
            if key in self.cache:
                result = copy.deepcopy(self.cache[key]); self.cache.move_to_end(key)
                result['cached'] = True
                return result
        context = build_context(trip)
        response, selected, error = None, None, None
        status = 'deterministic'
        try:
            client = self.client or LocalModelClient(LocalAIConfig.load())
            fitted, fits = fit_context(context, client.config)
            if not fits:
                error = 'Der notwendige Belegkontext passt nicht in das konfigurierte Kontextlimit.'
            elif not context['statements']:
                error = 'Keine ausreichend strukturierten Einzelbelege; keine Modellanfrage erforderlich.'
            elif not fitted['statements']:
                error = 'Im Kontextlimit bleibt kein Platz für Einzelbelege; die Belegübersicht wird ohne KI angezeigt.'
            else:
                context = fitted
                response = client.chat(messages(context), schema=contract(), cancel=cancel)
                selected = validate_selection(response['parsed'], context)
                status = 'local_ai'
        except InterruptedError:
            raise
        except (OSError, TimeoutError, ValueError) as exc:
            error = str(exc)
            status = 'rejected' if response is not None else 'unavailable'
        if cancel.is_set():
            raise InterruptedError('Erklärung abgebrochen.')
        result = dict(key=key, status=status, cached=False, error=error, **render(context, selected),
                      client_seconds=response.get('client_seconds') if response else None)
        # Retry connectivity/timeouts on another explicit click; cache successful
        # validated selection and semantic rejection's deterministic fallback only.
        if status in ('local_ai', 'rejected', 'deterministic'):
            with self.guard:
                self.cache[key] = copy.deepcopy(result)
                while len(self.cache) > 64:
                    self.cache.popitem(last=False)
        return result
