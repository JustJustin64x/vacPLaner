from __future__ import annotations
import copy
import queue
import sqlite3
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import webbrowser
from decimal import InvalidOperation
from .DashboardThemeManager import DashboardThemeManager
from .TripPresenter import TripPresenter, euros
from ...core.planning.SearchRequest import SearchRequest, INTERESTS, AMENITIES
from ...core.planning.SearchContext import SearchContext
from ...core.planning.DiscoveryService import DiscoveryService
from ...core.planning.RankingService import RankingService
from ...infrastructure.planning.DestinationCatalog import DestinationCatalog
from ...infrastructure.planning.OpenTravelProvider import OpenTravelProvider
from ...infrastructure.planning.TripStore import TripStore
from ...infrastructure.planning.TripPdfExporter import TripPdfExporter


class SurprisePlannerApplication:
    def __init__(self, store=None, provider=None):
        self.store=store or TripStore()
        self.catalog=DestinationCatalog()
        self.provider=provider or OpenTravelProvider(self.store)
        self.events=queue.Queue()
        self.generation=0
        self.context=None
        self.running=False
        self.trips={}
        self.saved_id=None
        self.active=None
        self.vars={}
        self.checks={}
        self.workers=[]
        self.closed=False

    def create_window(self):
        if tk.TkVersion < 8.6:
            raise RuntimeError('Tk 8.6 oder neuer benötigt. Bitte scripts/setup-macos.sh ausführen; Apple-System-Tk 8.5 rendert fehlerhaft.')
        self.root=tk.Tk()
        self.root.title('Überraschungsreise · Europa entdecken')
        self.root.geometry('1380x900')
        self.root.minsize(1050,720)
        self.theme=DashboardThemeManager()
        self.theme.apply_theme(self.root)
        style=ttk.Style(self.root)
        style.configure('TRadiobutton',background=self.theme.COLOR_BACKGROUND,foreground=self.theme.COLOR_TEXT_SECONDARY)
        style.map('TButton',background=[('disabled','#35394d')],foreground=[('disabled','#94a3b8')])
        header=ttk.Frame(self.root,padding=(18,12))
        header.pack(fill='x')
        ttk.Label(header,text='Europa entdecken',style='Header.TLabel').pack(side='left')
        ttk.Label(header,text='  Ein Ziel',style='SubHeader.TLabel').pack(side='left',padx=15)
        ttk.Radiobutton(header,text='Mehrere Ziele · später',state='disabled').pack(side='left')
        ttk.Label(header,text='Lokal · ohne laufende Kosten',style='SubHeader.TLabel').pack(side='right')
        panes=ttk.Panedwindow(self.root,orient='horizontal')
        panes.pack(fill='both',expand=True,padx=14)
        left=ttk.Frame(panes,width=400)
        right=ttk.Frame(panes)
        panes.add(left,weight=0)
        panes.add(right,weight=1)
        notebook=ttk.Notebook(left)
        notebook.pack(fill='both',expand=True)
        self.filter_tabs={}
        for name in ('Reise','Interessen','Details'):
            outer=ttk.Frame(notebook)
            notebook.add(outer,text=name)
            canvas=tk.Canvas(outer,bg=self.theme.COLOR_BACKGROUND,highlightthickness=0,width=390)
            scroll=ttk.Scrollbar(outer,orient='vertical',command=canvas.yview)
            canvas.configure(yscrollcommand=scroll.set)
            scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
            frame=ttk.Frame(canvas,padding=12)
            window=canvas.create_window((0,0),window=frame,anchor='nw')
            frame.bind('<Configure>',lambda e,c=canvas:c.configure(scrollregion=c.bbox('all')))
            canvas.bind('<Configure>',lambda e,c=canvas,w=window:c.itemconfigure(w,width=e.width))
            self.filter_tabs[name]=frame
        default=SearchRequest()
        f=self.filter_tabs['Reise']
        self._note(f,'1 · Rahmenbedingungen')
        for key,label in [('origin','Startort'),('address','Genaue Startadresse (optional, bleibt lokal)'),('earliest','Früheste Abreise · JJJJ-MM-TT'),('latest','Späteste Rückkehr · JJJJ-MM-TT'),('min_days','Kalendertage mindestens'),('max_days','Kalendertage höchstens'),('adults','Erwachsene'),('rooms','Zimmer'),('budget','Gruppenbudget · EUR')]:
            self._entry(f,key,label,getattr(default,key))
        self._note(f,'7 Kalendertage = 6 Nächte. Reisejahr steht im Datum. Budget ist eine weiche Grenze.')
        self._entry(f,'countries','Länder oder Ländercodes · Komma; leer = alle','')
        self._entry(f,'regions','Regionen · Komma; leer = alle','')
        self._entry(f,'excluded','Ausschlüsse: Orte, Länder, Codes oder Regionen','')
        ttk.Button(f,text='Unterstützte Länder und Regionen',command=self.show_coverage).pack(fill='x',pady=6)
        self._note(f,'2 · Verkehrsmittel')
        self._checkboxes(f,'modes',('Auto','Zug','Flug'),default.modes)
        self._entry(f,'max_hours','Max. Stunden je Richtung (leer = offen)','')
        self._note(f,'Zeitlimit gilt für die obere Modellschätzung; Hotelzufahrt unbekannt. Optionen ohne Zeitdaten werden ausgeschlossen.')
        f=self.filter_tabs['Interessen']
        self._note(f,'Interessen · 0 = unwichtig, 5 = sehr wichtig')
        for name in INTERESTS:
            self._entry(f,'interest:'+name,name,default.interests[name])
        self._note(f,'Gewichtung des Vergleichs · 0 bis 100')
        for name in default.weights:
            self._entry(f,'weight:'+name,name,1)
        self._note(f,'Die Summe wird auf 100 % normiert. Alle Gewichte 0: je 25 %. Fehlende Preise gelten nicht als günstig. Klima und Wetter werden nicht prognostiziert.')
        f=self.filter_tabs['Details']
        self._note(f,'Benzinautos · gleiche Werte für alle Fahrzeuge')
        for key,label in [('cars','Fahrzeuge'),('seats','Sitzplätze je Fahrzeug'),('consumption','Verbrauch je Fahrzeug · l/100 km'),('petrol','Benzinpreis · EUR/l (eigene Annahme)')]:
            self._entry(f,key,label,getattr(default,key))
        self._note(f,'Unterkunftstypen')
        self._checkboxes(f,'accommodation_types',('Hotel','Ferienwohnung','Camping'),default.accommodation_types)
        self._note(f,'Ausstattung · egal / Wunsch / Pflicht. Unbekannte Pflichtmerkmale schließen eine Unterkunft aus.')
        for name in AMENITIES:
            self._entry(f,'amenity:'+name,name,'egal',values=('egal','Wunsch','Pflicht'))
        self._entry(f,'max_center_km','Max. Zentrumsentfernung · km Luftlinie','')
        self._note(f,'Begrenzte Suche')
        for key,label in [('shortlist','Ziele untersuchen · 3 bis 12'),('request_budget','Maximale Quellenabfragen · 4 bis 40'),('timeout_seconds','Zeitlimit · 10 bis 600 Sekunden')]:
            self._entry(f,key,label,getattr(default,key))
        self._note(f,'Öffentliche Quellen: Ortsnamen an OSM, Ziele an Wikivoyage, Koordinaten an FOSSGIS. Keine Adressenübertragung. Max. eine Anfrage/Sekunde; Cache, kein Massenabruf.')
        ttk.Button(f,text='Nominatim-Nutzungsregeln',command=lambda:webbrowser.open('https://operations.osmfoundation.org/policies/nominatim/')).pack(fill='x',pady=4)
        actions=ttk.Frame(left,padding=(0,10))
        actions.pack(fill='x')
        self.search_button=ttk.Button(actions,text='Reiseziele entdecken',command=self.start_search)
        self.search_button.pack(side='left',fill='x',expand=True)
        self.cancel_button=ttk.Button(actions,text='Abbrechen',command=self.cancel_search,state='disabled')
        self.cancel_button.pack(side='left',padx=(8,0))
        self.output_tabs=ttk.Notebook(right)
        self.output_tabs.pack(fill='both',expand=True,padx=(12,0))
        results=ttk.Frame(self.output_tabs,padding=10)
        saved=ttk.Frame(self.output_tabs,padding=10)
        self.output_tabs.add(results,text='Reisevergleich')
        self.output_tabs.add(saved,text='Gespeicherte Reisen')
        self._note(results,'Echte Orte und Quellen · Preise und Belegung nur soweit nachweisbar. Keine Buchung in der App.')
        self.tree=ttk.Treeview(results,columns=('place','date','price','quality'),show='headings',height=7,selectmode='browse')
        for key,label,width in [('place','Reiseziel',140),('date','Termine',190),('price','Reisebasis / Lücken',230),('quality','Bewertung',85)]:
            self.tree.heading(key,text=label);self.tree.column(key,width=width,minwidth=65,stretch=True)
        self.tree.pack(fill='x',pady=(5,10))
        self.tree.bind('<<TreeviewSelect>>',self.select_trip)
        swaps=ttk.Frame(results);swaps.pack(fill='x',pady=4)
        ttk.Label(swaps,text='Unterkunft').grid(row=0,column=0,sticky='w')
        self.lodging_box=ttk.Combobox(swaps,state='readonly',width=30)
        self.lodging_box.grid(row=1,column=0,sticky='ew',padx=(0,8))
        self.lodging_box.bind('<<ComboboxSelected>>',self.swap)
        ttk.Label(swaps,text='Hin- und Rückreise').grid(row=0,column=1,sticky='w')
        self.transport_box=ttk.Combobox(swaps,state='readonly',width=16)
        self.transport_box.grid(row=1,column=1,sticky='ew')
        self.transport_box.bind('<<ComboboxSelected>>',self.swap)
        swaps.columnconfigure(0,weight=1)
        buttons=ttk.Frame(results);buttons.pack(fill='x',pady=8)
        ttk.Button(buttons,text='Reise speichern',command=self.save_trip).pack(side='left')
        ttk.Button(buttons,text='Als neue Reise speichern',command=lambda:self.save_trip(True)).pack(side='left',padx=6)
        ttk.Button(buttons,text='PDF exportieren',command=self.export_pdf).pack(side='left')
        textframe=ttk.Frame(results);textframe.pack(fill='both',expand=True)
        self.details=tk.Text(textframe,wrap='word',height=12)
        self.theme.style_text_widget(self.details)
        self.details.configure(font=('Helvetica',11),state='disabled')
        bar=ttk.Scrollbar(textframe,command=self.details.yview)
        self.details.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y');self.details.pack(fill='both',expand=True)
        self.details.tag_configure('heading',foreground='#7dd3fc',font=('Helvetica',13,'bold'),spacing1=14,spacing3=6)
        self.saved_tree=ttk.Treeview(saved,columns=('name','time'),show='headings',selectmode='browse')
        self.saved_tree.heading('name',text='Reisename');self.saved_tree.heading('time',text='Gespeichert (UTC)')
        self.saved_tree.pack(fill='both',expand=True)
        self.saved_tree.bind('<Double-1>',lambda e:self.open_saved())
        row=ttk.Frame(saved);row.pack(fill='x',pady=12)
        for label,command in [('Öffnen / ändern',self.open_saved),('Duplizieren',self.duplicate_saved),('Löschen',self.delete_saved)]:
            ttk.Button(row,text=label,command=command).pack(side='left',padx=4)
        statusframe=ttk.Frame(self.root,padding=(18,8));statusframe.pack(fill='x')
        self.status=tk.StringVar(value='Bereit. Europa umfasst die dokumentierte Auswahl von 65 Zielen; kein vollständiger Marktvergleich.')
        ttk.Label(statusframe,textvariable=self.status,wraplength=1250).pack(anchor='w')
        self.elapsed=tk.StringVar(value='')
        ttk.Label(statusframe,textvariable=self.elapsed,style='SubHeader.TLabel').pack(anchor='w')
        self.source_log=tk.Text(statusframe,height=3,wrap='word',font=('Helvetica',10),bg='#181824',fg='#e2e8f0',relief='flat')
        self.source_log.pack(fill='x');self.source_log.configure(state='disabled')
        self.refresh_saved()
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.root.after(150,self.poll)
        return self.root

    def _entry(self,parent,key,label,value,values=None):
        ttk.Label(parent,text=label,wraplength=350).pack(anchor='w',pady=(7,2))
        variable=tk.StringVar(value=str(value));self.vars[key]=variable
        widget=ttk.Combobox(parent,textvariable=variable,values=values,state='readonly') if values else ttk.Entry(parent,textvariable=variable)
        widget.pack(fill='x')

    def _note(self,parent,text):
        ttk.Label(parent,text=text,wraplength=350,style='SubHeader.TLabel').pack(anchor='w',pady=(8,4))

    def _checkboxes(self,parent,key,choices,selected):
        self.checks[key]={}
        for choice in choices:
            variable=tk.BooleanVar(value=choice in selected);self.checks[key][choice]=variable
            ttk.Checkbutton(parent,text=choice,variable=variable).pack(anchor='w',pady=2)

    def read_request(self):
        data={}
        integers={'min_days','max_days','adults','rooms','cars','seats','shortlist','request_budget','timeout_seconds'}
        lists={'countries','regions','excluded'}
        decimals={'budget','consumption','petrol','max_hours','max_center_km'}
        for key,var in self.vars.items():
            if ':' in key: continue
            value=var.get().strip()
            data[key]=int(value) if key in integers else [v.strip() for v in value.split(',') if v.strip()] if key in lists else value.replace(',','.') if key in decimals else value
        data['interests']={k:int(self.vars['interest:'+k].get()) for k in INTERESTS}
        data['weights']={k:int(self.vars['weight:'+k].get()) for k in ('Preis','Reisezeit','Komfort','Interessen')}
        data['required']=[k for k in AMENITIES if self.vars['amenity:'+k].get()=='Pflicht']
        data['desired']=[k for k in AMENITIES if self.vars['amenity:'+k].get()=='Wunsch']
        for key,choices in self.checks.items():data[key]=[k for k,v in choices.items() if v.get()]
        request=SearchRequest(**data);request.validate()
        return request

    def populate_request(self,request):
        for key,value in request.items():
            if key in self.vars:self.vars[key].set(', '.join(value) if isinstance(value,list) else str(value))
        for k,v in request['interests'].items():self.vars['interest:'+k].set(v)
        for k,v in request['weights'].items():self.vars['weight:'+k].set(v)
        for k in AMENITIES:self.vars['amenity:'+k].set('Pflicht' if k in request['required'] else 'Wunsch' if k in request['desired'] else 'egal')
        for key,choices in self.checks.items():
            for k,v in choices.items():v.set(k in request[key])

    def start_search(self):
        try:request=self.read_request()
        except (ValueError,InvalidOperation) as exc:
            messagebox.showerror('Eingaben prüfen',str(exc),parent=self.root);return
        if self.context:self.context.cancel.set()
        self.generation+=1;generation=self.generation
        context=SearchContext(seconds=request.timeout_seconds,budget=request.request_budget)
        self.context=context;self.running=True
        self.trips={};self.active=None;self.saved_id=None
        self.tree.delete(*self.tree.get_children())
        self.lodging_box.set('');self.lodging_box.configure(values=[])
        self.transport_box.set('');self.transport_box.configure(values=[])
        self.details.configure(state='normal');self.details.delete('1.0','end');self.details.configure(state='disabled')
        self.source_log.configure(state='normal');self.source_log.delete('1.0','end');self.source_log.configure(state='disabled')
        self.search_button.configure(state='disabled');self.cancel_button.configure(state='normal')
        self.output_tabs.select(0)
        def emit(kind,value):self.events.put((generation,kind,value))
        def work():
            try:
                DiscoveryService(self.catalog,self.provider).search(request,context,emit)
            except (InterruptedError,ValueError,OSError) as exc:emit('warning',str(exc))
            except Exception as exc:emit('warning','Suche wegen unerwartetem Fehler beendet: '+type(exc).__name__)
            finally:emit('done',None)
        worker=threading.Thread(target=work,name='travel-search',daemon=False)
        self.workers=[t for t in self.workers if t.is_alive()]+[worker];worker.start()

    def cancel_search(self):
        if self.context:self.context.cancel.set()
        # Invalidate queued/late results immediately, even if another search starts.
        self.generation+=1;self.running=False
        self.search_button.configure(state='normal');self.cancel_button.configure(state='disabled')
        self.status.set('Abgebrochen. Vorhandene Teilergebnisse bleiben erhalten.')

    def poll(self):
        if self.closed:return
        for _ in range(100):
            try:generation,kind,value=self.events.get_nowait()
            except queue.Empty:break
            if generation!=self.generation:continue
            if kind=='phase':self.status.set(value)
            elif kind=='warning':
                self.source_log.configure(state='normal');self.source_log.insert('end',value+'\n');self.source_log.see('end');self.source_log.configure(state='disabled')
            elif kind=='result':
                self.trips[value['id']]=value;self.update_row(value)
                if self.active is None:self.tree.selection_set(value['id']);self.select_trip()
            elif kind=='done':
                self.running=False;self.search_button.configure(state='normal');self.cancel_button.configure(state='disabled')
                self.status.set(f"Suche beendet · {len(self.trips)} Reiseziele. Quellenprobleme und Datenlücken bitte beachten.")
        if self.context:
            seconds=int(time.monotonic()-self.context.started)
            if self.running:self.elapsed.set(f'{seconds//60:02d}:{seconds%60:02d} verstrichen · {len(self.trips)} Ergebnisse · {self.context.calls}/{self.context.budget} Quellenabfragen')
        self.root.after(150,self.poll)

    def update_row(self,trip):
        s=trip['cost_summary']
        price=(s['status']+' '+euros(s['low'])+'–'+euros(s['high'])) if s['coverage'] else 'Preis unbekannt'
        if s['missing']:price+=' + Lücken'
        values=(trip['destination']['name'],trip['start']+' – '+trip['end'],price,str(trip['score']))
        if self.tree.exists(trip['id']):self.tree.item(trip['id'],values=values)
        else:self.tree.insert('','end',iid=trip['id'],values=values)
        for index,identifier in enumerate(sorted(self.trips,key=lambda k:self.trips[k]['score'],reverse=True)):
            self.tree.move(identifier,'',index)

    def select_trip(self,event=None):
        selection=self.tree.selection()
        if not selection:return
        if self.active is not self.trips[selection[0]]:self.saved_id=None
        self.active=self.trips[selection[0]]
        trip=self.active
        self.lodging_box.configure(values=[l['name'] for l in trip['lodgings']])
        if trip['lodgings']:self.lodging_box.current(trip['selected_lodging'])
        else:self.lodging_box.set('Keine Unterkunft gefunden')
        self.transport_box.configure(values=[t['mode'] for t in trip['transports']]);self.transport_box.current(trip['selected_transport'])
        self.show_details()

    def swap(self,event=None):
        if not self.active:return
        if self.active['lodgings']:self.active['selected_lodging']=max(0,self.lodging_box.current())
        self.active['selected_transport']=max(0,self.transport_box.current())
        RankingService.recompute(self.active);self.update_row(self.active);self.show_details()

    def show_details(self):
        self.details.configure(state='normal');self.details.delete('1.0','end')
        for tag in self.details.tag_names():
            if tag.startswith('link'):self.details.tag_delete(tag)
        index=0
        for heading,paragraphs,links in TripPresenter.sections(self.active):
            self.details.insert('end',heading+'\n','heading')
            for paragraph in paragraphs:self.details.insert('end',paragraph+'\n\n')
            for label,url in links:
                tag='link'+str(index);index+=1
                self.details.tag_configure(tag,foreground='#7dd3fc',underline=True)
                self.details.tag_bind(tag,'<Button-1>',lambda e,u=url:webbrowser.open(u))
                self.details.insert('end',label+' ↗\n',tag)
        self.details.configure(state='disabled');self.details.see('1.0')

    def save_trip(self,as_new=False):
        if not self.active:return
        name=simpledialog.askstring('Reise speichern','Name der Reise:',initialvalue=self.active.get('saved_name',self.active['destination']['name']+' '+self.active['start']),parent=self.root)
        if not name:return
        try:
            self.active['saved_name']=name
            self.saved_id=self.store.save(name,self.active,None if as_new else self.saved_id)
            self.refresh_saved();self.status.set('Reise dauerhaft gespeichert. Auswahl und damaliger Quellenstand bleiben erhalten.')
        except (ValueError,OSError,sqlite3.Error) as exc:messagebox.showerror('Speichern fehlgeschlagen',str(exc),parent=self.root)

    def refresh_saved(self):
        self.saved_tree.delete(*self.saved_tree.get_children())
        for item in self.store.list():self.saved_tree.insert('','end',iid=item['id'],values=(item['name'],item['saved_at']))

    def open_saved(self):
        selected=self.saved_tree.selection()
        if not selected:return
        if self.running:self.cancel_search()
        trip=self.store.load(selected[0]);RankingService.recompute(trip)
        self.trips[trip['id']]=trip;self.update_row(trip)
        self.tree.selection_set(trip['id']);self.select_trip();self.saved_id=selected[0]
        self.populate_request(trip['request']);self.output_tabs.select(0)
        self.status.set('Gespeicherter Stand geöffnet. Neue Suche verwendet geänderte Filter; gespeicherte Preise sind keine aktuellen Angebote.')

    def duplicate_saved(self):
        selected=self.saved_tree.selection()
        if not selected:return
        name=simpledialog.askstring('Duplizieren','Name der Kopie:',initialvalue=self.saved_tree.item(selected[0],'values')[0]+' – Kopie',parent=self.root)
        if name:self.store.duplicate(selected[0],name);self.refresh_saved()

    def delete_saved(self):
        selected=self.saved_tree.selection()
        if not selected:return
        if messagebox.askyesno('Gespeicherte Reise löschen','Diese gespeicherte Reise löschen?',parent=self.root):
            self.store.delete(selected[0]);self.refresh_saved()
            if self.saved_id==selected[0]:self.saved_id=None

    def export_pdf(self):
        if not self.active:return
        path=filedialog.asksaveasfilename(parent=self.root,defaultextension='.pdf',filetypes=[('PDF','*.pdf')],initialfile='Reise-'+self.active['destination']['name']+'.pdf')
        if path:
            try:
                TripPdfExporter().export(path,TripPresenter.sections(self.active));self.status.set('PDF lokal gespeichert: '+path)
            except Exception as exc:messagebox.showerror('PDF-Export fehlgeschlagen',str(exc),parent=self.root)

    def show_coverage(self):
        countries=sorted({d['country']+' ('+d['code']+')' for d in self.catalog.destinations})
        regions=sorted({d['region'] for d in self.catalog.destinations})
        messagebox.showinfo('Unterstützte Europaauswahl',f'{len(self.catalog.destinations)} kuratierte Ziele; keine vollständige Europaabdeckung.\n\nLänder: '+', '.join(countries)+'\n\nRegionen: '+', '.join(regions),parent=self.root)

    def close(self):
        self.closed=True
        if self.context:self.context.cancel.set()
        self.generation+=1
        self.root.destroy()

    def start_dashboard(self):
        self.create_window().mainloop()
