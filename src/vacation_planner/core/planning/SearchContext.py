import time
from threading import Event


class SearchContext:
    def __init__(self, cancel=None, seconds=300, budget=24):
        self.cancel = cancel or Event()
        self.started = time.monotonic()
        self.deadline = self.started+seconds
        self.budget = budget
        self.calls = 0
        self.disabled = set()

    def check(self):
        if self.cancel.is_set():
            raise InterruptedError('Suche abgebrochen; vorhandene Ergebnisse bleiben erhalten.')
        if time.monotonic() >= self.deadline:
            raise InterruptedError('Zeitlimit erreicht; vorhandene Teilergebnisse bleiben erhalten.')

    def consume(self):
        self.check()
        if self.calls >= self.budget:
            raise InterruptedError('Abfragebudget erreicht; vorhandene Teilergebnisse bleiben erhalten.')
        self.calls += 1

    def wait(self, seconds):
        self.check()
        self.cancel.wait(min(seconds,max(0,self.deadline-time.monotonic())))
        self.check()
