"""Tk-thread presentation with private worker mailbox and stale-result tokens."""
import copy
import queue
import threading
import tkinter as tk
from tkinter import ttk
import webbrowser
from ...infrastructure.local_ai.ExplanationService import ExplanationService, START_HINT


class ExplanationPanel:
    def __init__(self, app, parent, service=None):
        self.app = app
        self.service = service or ExplanationService()
        self.events = queue.Queue()
        self.key = None
        self.trip = None
        self.serial = 0
        self.cancel = None
        self.result = None
        self.frame = ttk.Frame(app.output_tabs, padding=12)
        app.output_tabs.add(self.frame, text='Passung erklären')
        self.button = ttk.Button(parent, text='Passung erklären', command=self.start, state='disabled')
        self.button.pack(side='left')
        self.cancel_button = ttk.Button(parent, text='Erklärung abbrechen', command=self.abort, state='disabled')
        self.cancel_button.pack(side='left', padx=6)
        self.heading = tk.StringVar(value='Wähle ein Reiseziel aus dem Vergleich.')
        ttk.Label(self.frame, textvariable=self.heading, font=('Helvetica', 14, 'bold'), wraplength=700).pack(anchor='w')
        self.status = tk.StringVar(value='Lokale KI auf Knopfdruck; die Suche funktioniert unabhängig davon.')
        ttk.Label(self.frame, textvariable=self.status, wraplength=700).pack(anchor='w', pady=8)
        ttk.Button(self.frame, text='Erklärung anzeigen / erstellen', command=self.start).pack(anchor='w', pady=(0,8))
        body = ttk.Frame(self.frame); body.pack(fill='both', expand=True)
        self.text = tk.Text(body, wrap='word', width=45, state='disabled')
        app.theme.style_text_widget(self.text)
        self.text.configure(state='disabled', font=('Helvetica', 11))
        scroll = ttk.Scrollbar(body, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y'); self.text.pack(fill='both', expand=True)

    def show(self, text, links=()):
        self.text.configure(state='normal'); self.text.delete('1.0', 'end')
        for tag in self.text.tag_names():
            if tag.startswith('source-'): self.text.tag_delete(tag)
        self.text.insert('end', text + '\n\n')
        for index, (label, url) in enumerate(links):
            tag = 'source-' + str(index)
            self.text.tag_configure(tag, foreground='#7dd3fc', underline=True)
            self.text.tag_bind(tag, '<Button-1>', lambda event, u=url: webbrowser.open(u))
            self.text.insert('end', label + ' ↗\n', tag)
        self.text.configure(state='disabled'); self.text.see('1.0')

    def sync(self, trip):
        key = self.service.key(trip) if trip else None
        if key == self.key: return
        self.abort(silent=True)
        self.key = key; self.trip = trip; self.result = None
        self.heading.set(('Passung: ' + trip['destination']['name']) if trip else 'Wähle ein Reiseziel aus dem Vergleich.')
        self.status.set('Noch keine Erklärung angefordert. Vorhandene Quelldaten bleiben maßgeblich.')
        self.show('Die lokale KI ordnet vorhandene Hinweise. Aussagen und Quellenzuordnung werden im Programm kontrolliert; fehlende Angaben bleiben sichtbar.')
        self.button.configure(state='normal' if trip else 'disabled')

    def start(self):
        if not self.trip or self.cancel is not None or self.app.closed: return
        self.app.output_tabs.select(self.frame)
        self.serial += 1; serial = self.serial; key = self.key
        cancel = threading.Event(); self.cancel = cancel
        original = copy.deepcopy(self.trip)
        self.status.set('Lokale KI ordnet die Belege … Abbrechen ist jederzeit möglich.')
        self.button.configure(state='disabled'); self.cancel_button.configure(state='normal')
        self.show('Erklärung wird erstellt. Bestehende Reiseinformationen sind im Reisevergleich weiter verfügbar.')
        def work():
            try:
                result = self.service.explain(original, cancel)
                self.events.put((serial, key, result, None))
            except InterruptedError:
                self.events.put((serial, key, None, 'Erklärung abgebrochen.'))
            except Exception:
                self.events.put((serial, key, None, 'Erklärung fehlgeschlagen. Die Reise bleibt unverändert; bitte erneut versuchen.'))
        worker = threading.Thread(target=work, name='local-trip-explanation', daemon=False)
        self.app.workers = [w for w in self.app.workers if w.is_alive()] + [worker]
        worker.start()

    def abort(self, silent=False):
        if self.cancel is not None: self.cancel.set()
        self.cancel = None; self.serial += 1
        self.button.configure(state='normal' if self.trip else 'disabled')
        self.cancel_button.configure(state='disabled')
        if not silent:
            self.status.set('Erklärung abgebrochen. Suche und Reiseangaben bleiben nutzbar.')
            self.show('Keine ungeprüfte Teilantwort übernommen.')

    def poll(self):
        for _ in range(100):
            try: serial, key, result, error = self.events.get_nowait()
            except queue.Empty: break
            if serial != self.serial or key != self.key: continue
            self.cancel = None
            self.button.configure(state='normal' if self.trip else 'disabled'); self.cancel_button.configure(state='disabled')
            if error:
                self.status.set(error); self.show('Keine ungeprüfte Teilantwort übernommen.'); continue
            self.result = result
            if result['status'] == 'local_ai':
                self.status.set('Lokale KI-Erklärung · KI ordnet vorhandene Hinweise; der Wortlaut ist fest an die Belege gebunden.' + (' Aus dieser Sitzung wiederverwendet.' if result['cached'] else ''))
            else:
                self.status.set('Belegübersicht ohne KI-Auswahl · ' + (result['error'] or 'Keine verwertbare Modellauswahl.') + ('\n' + START_HINT if 'nicht erreichbar' in (result['error'] or '') else ''))
            self.show(result['text'], result['links'])
