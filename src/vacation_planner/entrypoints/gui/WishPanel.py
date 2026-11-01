"""Local wish input, explicit preview selection and atomic form application."""
import queue
import gc
import threading
import tkinter as tk
from tkinter import ttk
from ...core.planning.TravelWishes import MAX_TEXT, apply_proposals, field_label
from ...infrastructure.local_ai.WishService import WishService


class WishPanel:
    def __init__(self,app,input_tabs,service=None):
        self.app=app;self.service=service or WishService();self.events=queue.Queue()
        self.serial=0;self.cancel=None;self.result=None;self.selected=set();self.applying=False;self.traces=[]
        self.input_frame=ttk.Frame(input_tabs,padding=12);input_tabs.add(self.input_frame,text='Wünsche')
        ttk.Label(self.input_frame,text='Reisewünsche beschreiben',font=('Helvetica',13,'bold')).pack(anchor='w')
        ttk.Label(self.input_frame,text=f'Dein Text wird nur lokal ausgewertet (max. {MAX_TEXT} Zeichen). Vorschläge ändern noch keine Suchkriterien.',wraplength=345).pack(anchor='w',pady=8)
        self.input=tk.Text(self.input_frame,height=9,width=35,wrap='word',undo=True)
        app.theme.style_text_widget(self.input);self.input.pack(fill='x')
        ttk.Label(self.input_frame,text='Beispiel: Wir sind 4 Erwachsene; wir benötigen 2 Zimmer; 6 Nächte; Gruppenbudget: 2.400 Euro; nur mit dem Zug.\n\nInteressen bitte ausdrücklich gewichten, z. B. Kultur: 4 von 5. Andere Formulierungen können eine manuelle Präzisierung erfordern.',wraplength=345).pack(anchor='w',pady=8)
        row=ttk.Frame(self.input_frame);row.pack(fill='x')
        self.start_button=ttk.Button(row,text='Wünsche auswerten',command=self.start);self.start_button.pack(side='left')
        self.cancel_button=ttk.Button(row,text='Abbrechen',command=self.abort,state='disabled');self.cancel_button.pack(side='left',padx=5)
        self.status=tk.StringVar(value='Manuelle Suche bleibt unabhängig von der KI nutzbar.')
        ttk.Label(self.input_frame,textvariable=self.status,wraplength=345).pack(anchor='w',pady=10)
        self.frame=ttk.Frame(app.output_tabs,padding=10);app.output_tabs.add(self.frame,text='Wunschvorschau')
        ttk.Label(self.frame,text='Vorschläge prüfen und einzeln auswählen',font=('Helvetica',14,'bold')).pack(anchor='w')
        ttk.Label(self.frame,text='Nichts ist vorausgewählt. Nicht genannte Felder bleiben unverändert; bestehende Vorgaben wurden nicht aus dem Text erkannt.',wraplength=700).pack(anchor='w',pady=8)
        table=ttk.Frame(self.frame);table.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(table,columns=('pick','field','old','new','quote'),show='headings',height=6,selectmode='extended')
        for key,label,width in [('pick','Übernehmen',80),('field','Feld',135),('old','Bisher',130),('new','Vorschlag / Operation',170),('quote','Originaltext',250)]:
            self.tree.heading(key,text=label);self.tree.column(key,width=width,minwidth=65,stretch=False)
        sy=ttk.Scrollbar(table,command=self.tree.yview);sx=ttk.Scrollbar(table,orient='horizontal',command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        self.tree.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew');table.rowconfigure(0,weight=1);table.columnconfigure(0,weight=1)
        self.tree.bind('<ButtonRelease-1>',self.click);self.tree.bind('<<TreeviewSelect>>',self.describe)
        actions=ttk.Frame(self.frame);actions.pack(fill='x',pady=8)
        ttk.Button(actions,text='Markierte Auswahl umschalten',command=self.toggle).pack(side='left')
        self.apply_button=ttk.Button(actions,text='Ausgewählte Vorschläge übernehmen',command=self.apply,state='disabled');self.apply_button.pack(side='left',padx=8)
        self.notes=tk.Text(self.frame,wrap='word',height=10,state='disabled')
        app.theme.style_text_widget(self.notes);self.notes.configure(state='disabled');self.notes.pack(fill='both',expand=True)
        self.input.bind('<<Modified>>',self.text_changed);self.input.edit_modified(False)
        for var in list(app.vars.values())+[v for choices in app.checks.values() for v in choices.values()]:
            name=var.trace_add('write',self.form_changed);self.traces.append((var,name))

    def snapshot(self):
        return dict(vars={k:v.get() for k,v in self.app.vars.items()},checks={k:{n:v.get() for n,v in choices.items()} for k,choices in self.app.checks.items()})

    def note(self,text):
        self.notes.configure(state='normal');self.notes.delete('1.0','end');self.notes.insert('end',text);self.notes.configure(state='disabled')

    def invalidate(self,message='Eingabe geändert. Bitte erneut auswerten.'):
        if self.cancel is not None:self.cancel.set()
        self.cancel=None;self.serial+=1;self.result=None;self.selected.clear()
        self.start_button.configure(state='normal');self.cancel_button.configure(state='disabled');self.apply_button.configure(state='disabled')
        self.tree.delete(*self.tree.get_children());self.status.set(message);self.note(message)

    def form_changed(self,*args):
        if not self.applying and (self.cancel is not None or self.result is not None):self.invalidate('Formular geändert. Alte Vorschau verworfen; bitte erneut auswerten.')

    def text_changed(self,event=None):
        if self.input.edit_modified():
            self.input.edit_modified(False)
            if self.cancel is not None or self.result is not None:self.invalidate('Wunschtext geändert. Bitte erneut auswerten.')

    def start(self):
        if self.cancel is not None or self.app.closed:return
        text=self.input.get('1.0','end-1c')
        from ...core.planning.TravelWishes import check_text
        try:check_text(text)
        except ValueError as exc:self.status.set(str(exc));return
        self.invalidate('Lokale KI wertet die Wünsche aus …');self.serial+=1;serial=self.serial
        cancel=threading.Event();self.cancel=cancel;snapshot=self.snapshot()
        self.start_button.configure(state='disabled');self.cancel_button.configure(state='normal');self.app.output_tabs.select(self.frame)
        # Flush modified state before worker result arrives; input changes still
        # invalidate via both event and exact snapshot comparison at poll/apply.
        self.input.edit_modified(False)
        def work():
            try:self.events.put((serial,text,snapshot,self.service.evaluate(text,cancel),None))
            except InterruptedError:self.events.put((serial,text,snapshot,None,'Wunschauswertung abgebrochen.'))
            except Exception as exc:
                # Never echo raw exception/model/source text into logs/diagnostics.
                if isinstance(exc,TimeoutError):message='Zeitlimit erreicht. Keine Vorschläge übernommen.'
                elif isinstance(exc,OSError):message='Lokaler KI-Dienst nicht erreichbar. Start im Projekt: .venv/bin/python scripts/local_ai.py start'
                elif isinstance(exc,ValueError):
                    detail=str(exc)
                    if 'Modell fehlt' in detail or 'nicht vorhanden' in detail:message='Lokales Modell fehlt. Bestand mit .venv/bin/python scripts/local_ai.py status prüfen. Kein Download gestartet.'
                    elif 'abgeschnitten' in detail:message='Antwort am Ausgabelimit abgeschnitten. Bitte weniger Wünsche auf einmal auswerten. Nichts übernommen.'
                    elif 'Kontextlimit' in detail:message='Text passt nicht in das konfigurierte Kontextlimit. Bitte selbst kürzen. Nichts übernommen.'
                    else:message='Antwort nicht überprüfbar. Bitte einzelne klare Aussagen formulieren und erneut auswerten. Formular und Text bleiben erhalten.'
                else:message='Auswertung fehlgeschlagen. Text und Formular bleiben erhalten.'
                self.events.put((serial,text,snapshot,None,message))
        # Collect disposed Tk graphs on the UI thread before a worker allocates.
        gc.collect()
        worker=threading.Thread(target=work,name='local-travel-wishes',daemon=False)
        self.app.workers=[w for w in self.app.workers if w.is_alive()]+[worker];worker.start()

    def abort(self):self.invalidate('Auswertung abgebrochen. Text und Formular bleiben erhalten.')

    def poll(self):
        for _ in range(100):
            try:serial,text,snapshot,result,error=self.events.get_nowait()
            except queue.Empty:break
            if serial!=self.serial:continue
            if text!=self.input.get('1.0','end-1c') or snapshot!=self.snapshot():self.invalidate();continue
            self.cancel=None;self.start_button.configure(state='normal');self.cancel_button.configure(state='disabled')
            if error:self.status.set(error);self.note(error);continue
            self.result=result;self.original_text=text;self.original_snapshot=snapshot
            for p in result['accepted']:
                self.tree.insert('','end',iid=p['id'],values=('☐',field_label(p['field']),self.old_value(p['field']),p['value']+' · '+{'set':'setzen','add':'ergänzen','remove':'entfernen'}[p['operation']],p['quote']))
            lines=['Lokale Auswertung: '+str(len(result['accepted']))+' unabhängig abgesicherte Vorschläge. Bitte auswählen und prüfen.']
            lines += [i['message']+'\nTextstelle: „'+i['quote']+'“' for i in result['issues']]
            lines += ['Nicht abgesichert: '+field_label(i['field'])+' · '+i['reason'] for i in result['rejected']]
            lines += ['Vom Modell ausgelassen/nicht korrekt zugeordnet: „'+q+'“. Bitte manuell prüfen.' for q in result['omitted']]
            if result['missing']:lines += ['Nicht eindeutig genannt (keine Änderung): '+', '.join(field_label(k) for k in result['missing'])+'.']
            self.base_notes='\n\n'.join(lines);self.note(self.base_notes)
            self.status.set("Bitte Wünsche präzisieren. Mehrdeutige Angaben bleiben unverändert; keine Modellanfrage erforderlich." if result.get("mode")=="clarification_without_model" else f"{len(result['accepted'])} Vorschläge, {len(result['rejected'])} verworfen. Noch nichts übernommen.")

    def old_value(self,field):
        v=self.app.vars
        if field=='period':return v['earliest'].get()+' bis '+v['latest'].get()
        if field=='duration_days':return v['min_days'].get()+'–'+v['max_days'].get()
        if field=='modes':return ', '.join(k for k,x in self.app.checks['modes'].items() if x.get())
        return v[field].get() if field in v else ''

    def click(self,event):
        if self.tree.identify_column(event.x)=='#1':
            row=self.tree.identify_row(event.y)
            if row:self.tree.selection_set(row);self.toggle()

    def toggle(self):
        if not self.result:return
        for cid in self.tree.selection():
            if cid in self.selected:self.selected.remove(cid)
            else:self.selected.add(cid)
            values=list(self.tree.item(cid,'values'));values[0]='☑' if cid in self.selected else '☐';self.tree.item(cid,values=values)
        self.apply_button.configure(state='normal' if self.selected else 'disabled')

    def describe(self,event=None):
        if not self.result:return
        ids=set(self.tree.selection());rows=[p for p in self.result['accepted'] if p['id'] in ids]
        detail='\n\n'.join(p['note']+'\nOriginaltext: „'+p['quote']+'“' for p in rows)
        self.note((detail+'\n\n' if detail else '')+self.base_notes)

    def apply(self):
        if not self.result or not self.selected:return
        if self.input.get('1.0','end-1c')!=self.original_text or self.snapshot()!=self.original_snapshot:self.invalidate();return
        try:
            base=self.app.read_request().to_dict()
            # Stable preview order, not arbitrary set iteration.
            ids=[p['id'] for p in self.result['accepted'] if p['id'] in self.selected]
            patched=apply_proposals(base,self.result['accepted'],ids)
        except (ValueError,ArithmeticError) as exc:
            self.status.set('Nicht übernommen: '+str(exc));return
        self.applying=True
        try:self.app.populate_request(patched)
        finally:self.applying=False
        self.invalidate(f'{len(ids)} ausgewählte Vorschläge übernommen. Suche bitte ausdrücklich starten.')

    def close(self):
        if self.cancel is not None:self.cancel.set()
        self.serial+=1;self.result=None
        for var,name in self.traces:var.trace_remove('write',name)
        self.traces.clear();self.app=None
