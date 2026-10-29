from __future__ import annotations
import copy
import json
from pathlib import Path
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
from ...infrastructure.planning.PdfTripPresenter import PdfTripPresenter
from ...infrastructure.planning.TripEnrichmentService import TripEnrichmentService


class ExportReadinessDialog:
    """Four explicit choices; kept separate so completeness logic is testable."""
    def __init__(self,parent,issues,multiple=False):
        self.result=None
        window=tk.Toplevel(parent);self.window=window;window.title('PDF-Export prüfen');window.transient(parent);window.grab_set();window.resizable(False,False)
        ttk.Label(window,text='Einige Reiseangaben sind noch offen.',font=('Helvetica',14,'bold')).pack(anchor='w',padx=18,pady=(16,6))
        ttk.Label(window,text='\n'.join('• '+x for x in issues),wraplength=520,justify='left').pack(anchor='w',padx=18,pady=6)
        ttk.Label(window,text='Ein fehlendes Bild verhindert den Export nicht.',wraplength=520).pack(anchor='w',padx=18,pady=(0,10))
        actions=ttk.Frame(window,padding=(14,8));actions.pack(fill='x')
        choices=[('Preise recherchieren / aktualisieren','research'),('Mit gekennzeichneten Lücken exportieren','export')]
        if multiple: choices.append(('Betroffene Reisen entfernen','remove'))
        choices.append(('Zurück zur Reiseplanung','back'))
        for label,value in choices:ttk.Button(actions,text=label,command=lambda v=value:self.finish(v)).pack(fill='x',pady=3)
        window.protocol('WM_DELETE_WINDOW',lambda:self.finish('back'));window.wait_window()
    def finish(self,value):
        self.result=value;self.window.grab_release();self.window.destroy()


class SurprisePlannerApplication:
    def __init__(self, store=None, provider=None):
        self.store=store or TripStore()
        from ...infrastructure.planning.DestinationInventory import DestinationInventory
        self.inventory=DestinationInventory(self.store.path.with_name('destinations.sqlite3'))
        self.catalog=DestinationCatalog(self.inventory)
        self.import_context=None
        self.provider=provider or OpenTravelProvider(self.store,catalog=self.catalog)
        if isinstance(self.provider,OpenTravelProvider):self.provider.catalog=self.catalog
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
        self.diagnostic=None
        self.export_order=[]
        self.enrichment_context=None
        self.media_photo=None
        self.price_context=None

    def create_window(self):
        if tk.TkVersion < 8.6:
            raise RuntimeError('Tk 8.6 oder neuer benötigt. Bitte scripts/setup-macos.sh ausführen; Apple-System-Tk 8.5 rendert fehlerhaft.')
        self.root=tk.Tk()
        self.root.title('Überraschungsreise · Europa entdecken')
        width=min(1380,max(1000,self.root.winfo_screenwidth()-80))
        height=min(900,max(650,self.root.winfo_screenheight()-120))
        self.root.geometry(f'{width}x{height}+20+40')
        self.root.minsize(1000,650)
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
        ttk.Button(f,text='Gebiete suchen und auswählen',command=self.show_coverage).pack(fill='x',pady=6)
        ttk.Button(f,text='Zieldaten einrichten / aktualisieren',command=self.setup_destinations).pack(fill='x',pady=4)
        self._entry(f,'target_type','Zieltypen','gemischt',values=('gemischt','Stadt','kleiner Ort','See/Küste','Berge/Natur'))
        self._note(f,'2 · Verkehrsmittel')
        self._checkboxes(f,'modes',('Auto','Zug','Flug'),default.modes)
        self._entry(f,'max_hours','Max. Stunden je Richtung (leer = offen)','')
        self._entry(f,'max_distance_km','Geografischer Suchradius · km Luftlinie (optional)','')
        self._note(f,'Zeitlimit gilt für die obere Modellschätzung. Unbekannte Zeiten sind keine Filtertreffer; offene Ideen können unter Details separat aktiviert werden.')
        f=self.filter_tabs['Interessen']
        self._note(f,'Interessen · 0 = unwichtig, 5 = sehr wichtig')
        for name in INTERESTS:
            self._entry(f,'interest:'+name,name,default.interests[name],values=tuple(range(6)))
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
        self._entry(f,'surroundings','Umgebungssuche','ja',values=('ja','nein'))
        self._entry(f,'lodging_radius_km','Unterkünfte: Umkreis · km Luftlinie (max. 50)',default.lodging_radius_km)
        self._entry(f,'activity_radius_km','Aktivitäten: Umkreis · km Luftlinie (max. 50)',default.activity_radius_km)
        self._entry(f,'show_ideas','Ideen mit unbelegten Pflichtangaben separat anzeigen','nein',values=('ja','nein'))
        self._entry(f,'regional_queries','Kleine regionale Zusatzabfragen · 0 bis 3',default.regional_queries)
        self._note(f,'Begrenzte Suche')
        for key,label in [('shortlist','Gewünschte Filtertreffer · 3 bis 12'),('candidate_pool','Vertiefte Kandidatenauswahl · 10 bis 100'),('price_targets','Preisrecherche für beste Ziele · 0 bis 12'),('request_budget','Maximale Quellenabfragen · 4 bis 40'),('timeout_seconds','Zeitlimit · 10 bis 600 Sekunden')]:
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
        self.tree=ttk.Treeview(results,columns=('place','date','price','quality'),show='headings',height=5,selectmode='browse')
        for key,label,width in [('place','Reiseziel',140),('date','Termine',190),('price','Reisebasis / Lücken',230),('quality','Bewertung',85)]:
            self.tree.heading(key,text=label);self.tree.column(key,width=width,minwidth=65,stretch=True)
        self.tree.pack(fill='x',pady=(5,10))
        self.tree.bind('<<TreeviewSelect>>',lambda e:self.select_trip(tree=self.tree))
        ttk.Label(results,text='Passende Reiseideen – Angaben noch offen (keine Filtertreffer)').pack(anchor='w')
        self.idea_tree=ttk.Treeview(results,columns=('place','date','price','quality'),show='headings',height=2,selectmode='browse')
        for key,label,width in [('place','Ziel / offene Kriterien',210),('date','Termine',160),('price','Reisebasis / Lücken',180),('quality','Bewertung',70)]:
            self.idea_tree.heading(key,text=label);self.idea_tree.column(key,width=width,minwidth=50)
        self.idea_tree.pack(fill='x',pady=4)
        self.idea_tree.bind('<<TreeviewSelect>>',lambda e:self.select_trip(tree=self.idea_tree))
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
        ttk.Button(buttons,text='Angaben & Bilder recherchieren',command=self.enrich_active).pack(side='left',padx=6)
        prices=ttk.Frame(results);prices.pack(fill='x',pady=(0,4))
        self.price_category=ttk.Combobox(prices,state='readonly',values=('Alle Preise','Unterkunft','Bahn','Flug','Aktivitäten'),width=16)
        self.price_category.current(0);self.price_category.pack(side='left')
        self.price_button=ttk.Button(prices,text='Angebote aktuell prüfen',command=self.research_prices)
        self.price_button.pack(side='left',padx=6)
        ttk.Button(prices,text='Weitere Terminproben prüfen',command=lambda:self.research_prices(samples=True)).pack(side='left')
        assistance=ttk.Frame(results);assistance.pack(fill='x')
        ttk.Button(assistance,text='Im Browser unterstützen',command=self.support_source).pack(side='left')
        ttk.Button(assistance,text='Quelle überspringen',command=self.skip_source).pack(side='left',padx=6)
        self.media_label=ttk.Label(results,text='')
        self.media_label.pack(fill='x',pady=(2,6))
        self.media_selector=ttk.Combobox(results,state='readonly')
        self.media_selector.pack(fill='x',pady=(0,6));self.media_selector.bind('<<ComboboxSelected>>',lambda event:self._select_media_image())
        textframe=ttk.Frame(results);textframe.pack(fill='both',expand=True)
        self.details=tk.Text(textframe,wrap='word',height=12,width=45)
        self.theme.style_text_widget(self.details)
        self.details.configure(font=('Helvetica',11),state='disabled')
        bar=ttk.Scrollbar(textframe,command=self.details.yview)
        self.details.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y');self.details.pack(fill='both',expand=True)
        self.details.tag_configure('heading',foreground='#7dd3fc',font=('Helvetica',13,'bold'),spacing1=14,spacing3=6)
        self.saved_tree=ttk.Treeview(saved,columns=('name','time'),show='headings',selectmode='extended')
        self.saved_tree.heading('name',text='Reisename');self.saved_tree.heading('time',text='Gespeichert (UTC)')
        self.saved_tree.pack(fill='both',expand=True)
        self.saved_tree.bind('<Double-1>',lambda e:self.open_saved())
        row=ttk.Frame(saved);row.pack(fill='x',pady=12)
        for label,command in [('Öffnen / ändern',self.open_saved),('Duplizieren',self.duplicate_saved),('Löschen',self.delete_saved)]:
            ttk.Button(row,text=label,command=command).pack(side='left',padx=4)
        export_frame=ttk.LabelFrame(saved,text='Gemeinsamer PDF-Export',padding=8);export_frame.pack(fill='x',pady=(0,8))
        self.export_list=tk.Listbox(export_frame,height=4,selectmode='browse');self.export_list.pack(side='left',fill='x',expand=True)
        export_buttons=ttk.Frame(export_frame);export_buttons.pack(side='left',padx=(8,0))
        for label,command in [('Auswahl hinzufügen',self.add_saved_to_export),('Nach oben',lambda:self.move_export(-1)),('Nach unten',lambda:self.move_export(1)),('Entfernen',self.remove_from_export),('Auswahl als PDF exportieren',self.export_saved_pdf)]:
            ttk.Button(export_buttons,text=label,command=command).pack(fill='x',pady=2)
        statusframe=ttk.Frame(self.root,padding=(18,8));statusframe.pack(fill='x')
        self.status=tk.StringVar(value=f'Bereit. {len(self.catalog.destinations)} belegte Katalogziele; Interessen sind Wünsche, keine Pflichtfilter.')
        ttk.Label(statusframe,textvariable=self.status,wraplength=1250).pack(anchor='w')
        self.elapsed=tk.StringVar(value='')
        ttk.Label(statusframe,textvariable=self.elapsed,style='SubHeader.TLabel').pack(anchor='w')
        self.source_log=tk.Text(statusframe,height=3,wrap='word',font=('Helvetica',10),bg='#181824',fg='#e2e8f0',relief='flat')
        self.source_log.pack(fill='x');self.source_log.configure(state='disabled')
        diagnostic_frame=ttk.Frame(self.output_tabs,padding=10)
        self.output_tabs.add(diagnostic_frame,text='Suchdiagnose')
        self.diagnostic_text=tk.Text(diagnostic_frame,wrap='word',state='disabled')
        self.diagnostic_text.pack(fill='both',expand=True)
        ttk.Button(diagnostic_frame,text='Diagnose ohne genaue Adresse exportieren',command=self.export_diagnostic).pack(anchor='w')
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
        integers={'min_days','max_days','adults','rooms','cars','seats','shortlist','request_budget','timeout_seconds','price_targets','candidate_pool','regional_queries'}
        lists={'countries','regions','excluded'}
        decimals={'budget','consumption','petrol','max_hours','max_center_km','lodging_radius_km','activity_radius_km','max_distance_km'}
        for key,var in self.vars.items():
            if ':' in key: continue
            value=var.get().strip()
            if key in ('surroundings','show_ideas'):
                data[key]=value=='ja';continue
            data[key]=int(value) if key in integers else [v.strip() for v in value.split(',') if v.strip()] if key in lists else value.replace(',','.') if key in decimals else value
        data['interests']={k:float(self.vars['interest:'+k].get().replace(',','.')) for k in INTERESTS}
        data['weights']={k:float(self.vars['weight:'+k].get().replace(',','.')) for k in ('Preis','Reisezeit','Komfort','Interessen')}
        data['required']=[k for k in AMENITIES if self.vars['amenity:'+k].get()=='Pflicht']
        data['desired']=[k for k in AMENITIES if self.vars['amenity:'+k].get()=='Wunsch']
        for key,choices in self.checks.items():data[key]=[k for k,v in choices.items() if v.get()]
        request=SearchRequest(**data);request.validate()
        return request

    def populate_request(self,request):
        request={**SearchRequest().to_dict(),**request}
        for key,value in request.items():
            if key in self.vars:self.vars[key].set(('ja' if value else 'nein') if isinstance(value,bool) else ', '.join(value) if isinstance(value,list) else str(value))
        for k in INTERESTS:self.vars['interest:'+k].set(request['interests'].get(k,0))
        for k in ('Preis','Reisezeit','Komfort','Interessen'):self.vars['weight:'+k].set(request['weights'].get(k,0))
        for k in AMENITIES:self.vars['amenity:'+k].set('Pflicht' if k in request['required'] else 'Wunsch' if k in request['desired'] else 'egal')
        for key,choices in self.checks.items():
            for k,v in choices.items():v.set(k in request[key])

    def start_search(self):
        try:request=self.read_request()
        except (ValueError,InvalidOperation) as exc:
            messagebox.showerror('Eingaben prüfen',str(exc),parent=self.root);return
        if self.context:self.context.cancel.set()
        if self.price_context:self.price_context.cancel.set();self.price_context=None
        self.price_button.configure(state='normal')
        self.generation+=1;generation=self.generation
        context=SearchContext(seconds=request.timeout_seconds,budget=request.request_budget)
        self.context=context;self.running=True
        self.trips={};self.active=None;self.saved_id=None;self.diagnostic=None
        self.tree.delete(*self.tree.get_children())
        self.idea_tree.delete(*self.idea_tree.get_children())
        self.lodging_box.set('');self.lodging_box.configure(values=[])
        self.transport_box.set('');self.transport_box.configure(values=[])
        self.details.configure(state='normal');self.details.delete('1.0','end');self.details.configure(state='disabled')
        self.source_log.configure(state='normal');self.source_log.delete('1.0','end');self.source_log.configure(state='disabled')
        self.search_button.configure(state='disabled');self.cancel_button.configure(state='normal')
        self.output_tabs.select(0)
        def emit(kind,value):
            if kind=='diagnostic':
                try:
                    folder=self.store.path.parent/'diagnostics';folder.mkdir(exist_ok=True)
                    (folder/(value['search_id']+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2))
                except OSError:
                    self.events.put((generation,'warning','Diagnose konnte nicht lokal gespeichert werden; Export bleibt verfügbar.'))
            self.events.put((generation,kind,value))
        def work():
            try:
                if self.catalog.inventory is self.inventory:
                    emit('phase','Lokalen Zielbestand laden; keine Länderdownloads während der Suche.')
                    self.catalog.refresh(context)
                DiscoveryService(self.catalog,self.provider).search(request,context,emit)
            except (InterruptedError,ValueError,OSError) as exc:emit('warning',str(exc))
            except Exception:emit('warning','Unerwarteter Suchfehler. Details mit Such-ID stehen im Reiter Suchdiagnose.')
            finally:emit('done',None)
        worker=threading.Thread(target=work,name='travel-search',daemon=False)
        self.workers=[t for t in self.workers if t.is_alive()]+[worker];worker.start()

    def cancel_search(self):
        if self.context:self.context.cancel.set()
        if self.enrichment_context:self.enrichment_context.cancel.set();self.enrichment_context=None
        if self.price_context:self.price_context.cancel.set();self.price_context=None
        self.price_button.configure(state='normal')
        # Invalidate queued/late results immediately, even if another search starts.
        self.generation+=1;self.running=False
        self.search_button.configure(state='normal');self.cancel_button.configure(state='disabled')
        self.status.set('Abgebrochen. Vorhandene Teilergebnisse bleiben erhalten. Diagnose kann nach Ende des Workers exportiert werden.')

    def poll(self):
        if self.closed:return
        for _ in range(100):
            try:generation,kind,value=self.events.get_nowait()
            except queue.Empty:break
            if generation!=self.generation:continue
            if kind=='phase':self.status.set(value)
            elif kind=='warning':
                self.source_log.configure(state='normal');self.source_log.insert('end',value+'\n');self.source_log.see('end');self.source_log.configure(state='disabled')
            elif kind in ('result','offer_partial'):
                previous=self.trips.get(value['id'])
                if previous:
                    value['selected_lodging']=previous['selected_lodging'];value['selected_transport']=previous['selected_transport'];RankingService.recompute(value)
                self.trips[value['id']]=value;self.update_row(value)
                if self.active is not None and self.active['id']==value['id']:
                    self.active=value;self.refresh_trip_choices();self.show_details()
                if self.active is None:
                    tree=self.idea_tree if value.get('filter_status')=='offen' else self.tree
                    tree.selection_set(value['id']);self.select_trip(tree=tree)
            elif kind=='diagnostic':
                self.diagnostic=value
                self.diagnostic_text.configure(state='normal');self.diagnostic_text.delete('1.0','end')
                self.diagnostic_text.insert('end',value['summary']+'\n\n'+json.dumps(value,ensure_ascii=False,indent=2))
                self.diagnostic_text.configure(state='disabled')
            elif kind=='done':
                self.running=False;self.search_button.configure(state='normal');self.cancel_button.configure(state='disabled')
                self.status.set(self.diagnostic['summary'] if self.diagnostic else f'Suche beendet · {len(self.trips)} Reiseideen. Hinweise beachten.')
            elif kind=='enrich_phase':self.status.set(value)
            elif kind=='enrich_warning':
                self.source_log.configure(state='normal');self.source_log.insert('end',value+'\n');self.source_log.see('end');self.source_log.configure(state='disabled')
            elif kind=='enrich_result':
                self.active=value;self.trips[value['id']]=value;self.show_details()
                self.status.set('Nachrecherche abgeschlossen. Die Arbeitskopie wurde ergänzt; zum dauerhaften Bewahren ausdrücklich speichern.')
            elif kind=='enrich_done':self.enrichment_context=None;self.cancel_button.configure(state='disabled')
            elif kind=='price_phase':self.status.set(value)
            elif kind=='price_warning':
                self.source_log.configure(state='normal');self.source_log.insert('end',value+'\n');self.source_log.see('end');self.source_log.configure(state='disabled')
            elif kind in ('price_result','price_offer_partial'):
                previous=self.trips.get(value['id'])
                if previous:
                    value['selected_lodging']=previous['selected_lodging'];value['selected_transport']=previous['selected_transport'];RankingService.recompute(value)
                self.trips[value['id']]=value;self.update_row(value)
                if self.active is not None and self.active['id']==value['id']:
                    self.active=value;self.refresh_trip_choices();self.show_details()
                self.status.set('Preisprüfung abgeschlossen. Details zeigen Anbieterstatus und Preisstand. Zum Bewahren ausdrücklich speichern.')
            elif kind=='price_done':
                self.price_context=None;self.price_button.configure(state='normal');self.cancel_button.configure(state='disabled')
            elif kind=='price_export_ready':
                self._export_trips(value[0],value[1])
        if self.context:
            seconds=int(time.monotonic()-self.context.started)
            if self.running:
                c=getattr(self.context,'diagnostics',{}).get('counts',{})
                self.elapsed.set(f"{seconds//60:02d}:{seconds%60:02d} · {c.get('locally_scored',0)} lokal bewertet · {c.get('examined',0)} näher geprüft · {len(self.trips)} Ideen · {self.context.calls}/{self.context.budget} HTTP-Abfragen")
                prices=getattr(self.context,'price_context',None)
                if prices:self.elapsed.set(self.elapsed.get()+f' · Preise {prices.calls}/{prices.budget} Abfragen')
        self.root.after(150,self.poll)

    def update_row(self,trip):
        s=trip['cost_summary']
        price=(s['status']+' '+euros(s['low'])+'–'+euros(s['high'])) if s['coverage'] else 'Preis unbekannt'
        if s['missing']:price+=' + Lücken'
        tree=self.idea_tree if trip.get('filter_status')=='offen' else self.tree
        label=trip['destination']['name']+' · '+trip['destination'].get('type','Ort')
        if trip.get('open_criteria'):label+=' · '+trip['open_criteria'][0]
        values=(label,trip['start']+' – '+trip['end'],price,str(trip['score']))
        if tree.exists(trip['id']):tree.item(trip['id'],values=values)
        else:tree.insert('','end',iid=trip['id'],values=values)
        for widget in (self.tree,self.idea_tree):
            for index,identifier in enumerate(sorted(widget.get_children(),key=lambda k:self.trips[k]['score'],reverse=True)):
                widget.move(identifier,'',index)

    def select_trip(self,event=None,tree=None):
        tree=tree or self.tree
        selection=tree.selection()
        if not selection:return
        if self.active is not self.trips[selection[0]]:self.saved_id=None
        self.active=self.trips[selection[0]]
        self.refresh_trip_choices();self.show_details()

    def refresh_trip_choices(self):
        trip=self.active
        self.lodging_box.configure(values=[l['name'] for l in trip['lodgings']])
        if trip['lodgings']:self.lodging_box.current(trip['selected_lodging'])
        else:self.lodging_box.set('Keine Unterkunft gefunden')
        labels=[]
        for option in trip['transports']:
            offer=option.get('offer') or {};legs=offer.get('details',{}).get('legs',[])
            label=option['mode']
            if offer:label+=' · '+offer['provider']+(' · '+legs[0]['departure'][:16] if legs and legs[0].get('departure') else '')
            if option.get('offer_refresh_status') in ('found','no_offers'):label+=' · nicht mehr bestätigt'
            labels.append(label)
        self.transport_box.configure(values=labels);self.transport_box.current(trip['selected_transport'])

    def swap(self,event=None):
        if not self.active:return
        if self.active['lodgings']:self.active['selected_lodging']=max(0,self.lodging_box.current())
        self.active['selected_transport']=max(0,self.transport_box.current())
        RankingService.recompute(self.active);self.update_row(self.active);self.show_details()

    def show_details(self):
        self._show_active_image()
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

    def _show_active_image(self):
        self.media_photo=None;self.media_label.configure(image='',text='');self._media_items=[]
        if not self.active:self.media_selector.configure(values=[]);self.media_selector.set('');return
        destination=self.active.get('destination') or {}
        for label,item in [('Ziel · '+destination.get('name','Reiseziel'),destination)]:
            if (item.get('image') or {}).get('cache_path'):self._media_items.append((label,item['image']))
        for group,label in ((self.active.get('lodgings') or [],'Unterkunft'),(self.active.get('activities') or [],'Aktivität')):
            for item in group:
                if (item.get('image') or {}).get('cache_path'):self._media_items.append((label+' · '+item.get('name',''),item['image']))
        self.media_selector.configure(values=[x[0] for x in self._media_items])
        if not self._media_items:self.media_selector.set('Keine eindeutig zugeordneten Bilder im Cache');return
        self.media_selector.current(0);self._select_media_image()

    def _select_media_image(self):
        if not getattr(self,'_media_items',None):return
        index=max(0,self.media_selector.current());image=self._media_items[index][1]
        try:
            from PIL import Image,ImageTk
            source=Image.open(image['cache_path']);source.thumbnail((720,180));self.media_photo=ImageTk.PhotoImage(source);self.media_label.configure(image=self.media_photo)
        except (OSError,ValueError):self.media_label.configure(text='Bild konnte nicht angezeigt werden.')

    def enrich_active(self):
        if not self.active or self.running:return
        if self.enrichment_context:self.enrichment_context.cancel.set()
        context=SearchContext(seconds=90,budget=18);self.enrichment_context=context;original=self.active;generation=self.generation
        self.status.set('Gezielte Nachrecherche läuft …');self.cancel_button.configure(state='normal')
        def emit(kind,value):self.events.put((generation,'enrich_'+kind,value))
        def work():
            try:emit('result',TripEnrichmentService(self.store,self.provider.http).enrich(original,context,emit))
            except InterruptedError:emit('warning','Nachrecherche abgebrochen; vorhandene Reise bleibt erhalten.')
            except Exception as exc:emit('warning','Nachrecherche fehlgeschlagen: '+str(exc))
            finally:emit('done',None)
        worker=threading.Thread(target=work,name='trip-enrichment',daemon=False);self.workers.append(worker);worker.start()

    def research_prices(self,samples=False,trips=None,export_filename=None):
        if not self.active or self.running or self.price_context:return
        if not callable(getattr(self.provider,'research_offers',None)):
            messagebox.showinfo('Angebotsprüfung','Der gewählte Datenprovider unterstützt keine Angebotsprüfung.',parent=self.root);return
        context=SearchContext(seconds=600,budget=40);self.price_context=context
        originals=copy.deepcopy(trips or [self.active]);generation=self.generation
        mapping={'Alle Preise':None,'Unterkunft':['lodging'],'Bahn':['rail'],'Flug':['flight'],'Aktivitäten':['activities']}
        categories=None if trips else mapping.get(self.price_category.get());self.price_button.configure(state='disabled');self.cancel_button.configure(state='normal')
        def emit(kind,value):self.events.put((generation,'price_'+kind,value))
        def work():
            checked=copy.deepcopy(originals)
            try:
                for index,original in enumerate(originals):
                    context.check()
                    updated=self.provider.research_offers(original,context,emit,categories,samples=samples)
                    checked[index]=updated;emit('result',updated)
            except Exception as exc:emit('warning','Preisprüfung fehlgeschlagen: '+str(exc))
            finally:
                emit('done',None)
                if export_filename and checked and not context.cancel.is_set():emit('export_ready',(checked,export_filename))
        worker=threading.Thread(target=work,name='offer-research',daemon=False);self.workers.append(worker);worker.start()

    def support_source(self):
        if not self.active:return
        category={'Unterkunft':'lodging','Bahn':'rail','Flug':'flight','Aktivitäten':'activities'}.get(self.price_category.get(),'flight')
        result=self.active.get('offer_searches',{}).get(category,{})
        sources=result.get('sources') or []
        url=next((s for s in sources if isinstance(s,str) and s.startswith('https://') and '/restapi/' not in s),None)
        if not url:
            url={'flight':'https://www.google.com/travel/flights','rail':'https://www.bahn.de/buchung/start','lodging':'https://www.apartments-innsbruck.com/en/buchen/' if self.active['destination']['name']=='Innsbruck' else None}.get(category)
        if url:
            import webbrowser
            webbrowser.open(url)
            self.status.set('Quelle auf ausdrückliche Aktion geöffnet. Manuelle Prüfung; Preise werden nicht automatisch übernommen. Unabhängige Abfragen laufen weiter.')
        else:self.status.set('Keine geprüfte interaktive Quelle vorhanden. Preis bleibt offen; andere Quellen können weiterlaufen.')

    def skip_source(self):
        if not self.active:return
        category={'Unterkunft':'lodging','Bahn':'rail','Flug':'flight','Aktivitäten':'activities'}.get(self.price_category.get(),'flight')
        self.active.setdefault('skipped_offer_categories',[])
        if category not in self.active['skipped_offer_categories']:self.active['skipped_offer_categories'].append(category)
        if self.price_context:
            if not hasattr(self.price_context,'skipped_categories'):self.price_context.skipped_categories=set()
            self.price_context.skipped_categories.add(category)
        self.status.set('Quelle übersprungen. Andere Kategorien laufen weiter; gezielte Aktualisierung kann diese Kategorie erneut prüfen.')

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

    def add_saved_to_export(self):
        known={identifier for identifier,_ in self.export_order}
        for identifier in self.saved_tree.selection():
            if identifier not in known:self.export_order.append((identifier,self.saved_tree.item(identifier,'values')[0]));known.add(identifier)
        self._refresh_export_list()

    def _refresh_export_list(self):
        self.export_list.delete(0,'end')
        for _,name in self.export_order:self.export_list.insert('end',name)

    def move_export(self,direction):
        selection=self.export_list.curselection()
        if not selection:return
        old=selection[0];new=max(0,min(len(self.export_order)-1,old+direction))
        if new==old:return
        item=self.export_order.pop(old);self.export_order.insert(new,item);self._refresh_export_list();self.export_list.selection_set(new)

    def remove_from_export(self):
        selection=self.export_list.curselection()
        if selection:self.export_order.pop(selection[0]);self._refresh_export_list()

    def open_saved(self):
        selected=self.saved_tree.selection()
        if not selected:return
        if self.running:self.cancel_search()
        trip=self.store.load(selected[0]);RankingService.recompute(trip)
        self.trips[trip['id']]=trip;self.update_row(trip)
        tree=self.idea_tree if trip.get('filter_status')=='offen' else self.tree
        tree.selection_set(trip['id']);self.select_trip(tree=tree);self.saved_id=selected[0]
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
        self._export_trips([self.active],'Reise-'+self.active['destination']['name']+'.pdf')

    def export_saved_pdf(self):
        if not self.export_order:
            messagebox.showinfo('Reisen auswählen','Gespeicherte Reisen markieren und „Auswahl hinzufügen“ wählen.',parent=self.root);return
        trips=[]
        for identifier,_ in self.export_order:
            try:trips.append(self.store.load(identifier))
            except (KeyError,ValueError,sqlite3.Error):continue
        self._export_trips(trips,'Reisevergleich.pdf')

    def _export_trips(self,trips,initialfile):
        if not trips:return
        incomplete=[(trip,PdfTripPresenter.completeness(trip)) for trip in trips if not PdfTripPresenter.completeness(trip).complete]
        if incomplete and self.root.winfo_viewable():
            labels=[]
            for trip,status in incomplete:labels.append(trip.get('destination',{}).get('name','Reise')+': '+'; '.join(status.issues))
            action=ExportReadinessDialog(self.root,labels,len(trips)>1).result
            if action=='back' or not action:return
            if action=='remove':trips=[trip for trip in trips if PdfTripPresenter.completeness(trip).complete]
            if action=='research':
                if not self.active:self.active=trips[0]
                self.research_prices(trips=trips,export_filename=initialfile)
                return
        if not trips:
            messagebox.showinfo('Keine exportierbare Reise','Nach dem Entfernen unvollständiger Reisen ist die Auswahl leer.',parent=self.root);return
        path=filedialog.asksaveasfilename(parent=self.root,defaultextension='.pdf',filetypes=[('PDF','*.pdf')],initialfile=initialfile)
        if path:
            try:
                TripPdfExporter().export_trips(path,trips,'Unsere Reiseideen' if len(trips)>1 else 'Reiseführer · '+trips[0]['destination']['name']);self.status.set('PDF lokal gespeichert: '+path)
            except Exception as exc:messagebox.showerror('PDF-Export fehlgeschlagen',str(exc),parent=self.root)

    def export_diagnostic(self):
        report=self.diagnostic or getattr(self.context,'diagnostics',None)
        if not report:return
        path=filedialog.asksaveasfilename(parent=self.root,defaultextension='.json',filetypes=[('JSON','*.json')],initialfile='Suchdiagnose-'+report['search_id']+'.json')
        if path:Path(path).write_text(json.dumps(report,ensure_ascii=False,indent=2))

    def show_coverage(self):
        window=tk.Toplevel(self.root);window.title('Unterstützte Gebiete suchen');window.geometry('540x420')
        query=tk.StringVar();kind=tk.StringVar(value='regions')
        ttk.Label(window,text='Suchen, Eintrag auswählen und übernehmen. Mehrere Werte bleiben möglich.').pack(pady=8)
        ttk.Entry(window,textvariable=query).pack(fill='x',padx=12)
        for value,label in [('regions','Region'),('countries','Land'),('excluded','Ausschluss')]:
            ttk.Radiobutton(window,text=label,variable=kind,value=value).pack(anchor='w',padx=12)
        listing=tk.Listbox(window);listing.pack(fill='both',expand=True,padx=12)
        def refresh(*args):
            from ...infrastructure.planning.DestinationCatalog import normalize
            listing.delete(0,'end')
            for label in self.catalog.supported(kind.get()):
                if normalize(query.get()) in normalize(label):listing.insert('end',label)
        def apply():
            if not listing.curselection():return
            value=listing.get(listing.curselection()[0]);var=self.vars[kind.get()]
            existing=[s.strip() for s in var.get().split(',') if s.strip()]
            if value not in existing:existing.append(value)
            var.set(', '.join(existing));window.destroy()
        query.trace_add('write',refresh);kind.trace_add('write',refresh);refresh()
        ttk.Button(window,text='Auswahl übernehmen',command=apply).pack(pady=8)

    def close(self):
        self.closed=True
        if self.import_context:self.import_context.cancel.set()
        if self.context:self.context.cancel.set()
        if self.enrichment_context:self.enrichment_context.cancel.set()
        if self.price_context:self.price_context.cancel.set()
        self.generation+=1
        self.root.destroy()

    def start_dashboard(self):
        self.create_window().mainloop()

    def setup_destinations(self):
        if self.running or self.price_context or self.import_context:
            messagebox.showinfo('Recherche läuft','Laufende Recherche zuerst beenden oder abbrechen.',parent=self.root);return
        from .DestinationSetupDialog import DestinationSetupDialog
        DestinationSetupDialog(self)
