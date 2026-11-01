"""Explicit setup; its downloads never run merely because the application starts."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from ...core.planning.SearchContext import SearchContext
from ...infrastructure.planning.DestinationImportService import DestinationImportService, COUNTRIES, REGIONS, EXTRACTS
from ...infrastructure.planning.DestinationCatalog import DestinationCatalog


class DestinationSetupDialog:
    def __init__(self,app):
        self.app=app;self.events=queue.Queue();self.context=None;self.close_requested=False
        self.window=tk.Toplevel(app.root);self.window.title('Zieldaten einrichten und aktualisieren');self.window.geometry('800x'+str(min(800,app.root.winfo_screenheight()-100)))
        outer=ttk.Frame(self.window);outer.pack(fill='both',expand=True)
        canvas=tk.Canvas(outer,bg=app.theme.COLOR_BACKGROUND,highlightthickness=0)
        scrollbar=ttk.Scrollbar(outer,orient='vertical',command=canvas.yview);canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
        frame=ttk.Frame(canvas,padding=14);window=canvas.create_window((0,0),window=frame,anchor='nw')
        frame.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
        ttk.Label(frame,text='Geografischer Grundbestand und regionale Freizeitmerkmale',font=('Helvetica',14,'bold')).pack(anchor='w')
        ttk.Label(frame,text='Länderdateien von GeoNames enthalten auch Dörfer ohne Einwohnergrenze. Je Land können einige bis mehrere zehn MiB anfallen; große Länder benötigen mehr lokalen Speicher.\nDer Import läuft getrennt von der Reisesuche. Vorhandene Reisen bleiben unverändert. Alte Zieldaten bleiben bis zum erfolgreichen Austausch nutzbar.',wraplength=730,justify='left').pack(anchor='w',pady=8)
        self.coverage=tk.Text(frame,height=10,wrap='word');self.coverage.pack(fill='x')
        self.countries=tk.StringVar(value=', '.join(COUNTRIES))
        ttk.Label(frame,text='Europäische Länder als Codes, durch Kommas getrennt:').pack(anchor='w',pady=(10,0))
        ttk.Entry(frame,textvariable=self.countries).pack(fill='x')
        ttk.Button(frame,text='Länder nach Namen auswählen …',command=self.choose_countries).pack(anchor='w',pady=3)
        controls=ttk.Frame(frame);controls.pack(fill='x',pady=5)
        self.import_button=ttk.Button(controls,text='Ortsbestand einrichten / fortsetzen',command=self.import_countries);self.import_button.pack(side='left')
        ttk.Button(controls,text='Alle unterstützten Länder auswählen',command=lambda:self.countries.set(', '.join(COUNTRIES))).pack(side='left',padx=6)
        ttk.Button(frame,text='Ausgewählte Länder auf neuen Stand aktualisieren',command=lambda:self.import_countries(refresh=True)).pack(anchor='w')
        ttk.Button(frame,text='Fehlende Freizeitdaten im aktuellen Suchgebiet ergänzen',command=self.fill_search_area).pack(anchor='w',pady=4)
        self.region=ttk.Combobox(frame,state='readonly',values=list(REGIONS));self.region.current(3);self.region.pack(fill='x',pady=(10,3))
        ttk.Label(frame,text='Oder eigene Region: Name und Süd, West, Nord, Ost (Dezimalpunkt; höchstens 1 × 1 Grad).').pack(anchor='w')
        custom=ttk.Frame(frame);custom.pack(fill='x');self.region_name=tk.StringVar();self.bounds=tk.StringVar()
        ttk.Entry(custom,textvariable=self.region_name,width=24).pack(side='left');ttk.Entry(custom,textvariable=self.bounds).pack(side='left',fill='x',expand=True,padx=5)
        self.region_button=ttk.Button(frame,text='Regionale OSM-Merkmale aktualisieren',command=self.update_region);self.region_button.pack(anchor='w',pady=5)
        self.extract_button=ttk.Button(frame,text='Freizeitdaten für ausgewählte Region laden / aktualisieren',command=self.import_extract);self.extract_button.pack(anchor='w')
        ttk.Button(frame,text='Bereits heruntergeladene Datei für gewählten / eigenen Ausschnitt verwenden',command=self.import_local).pack(anchor='w',pady=3)
        self.progress=tk.StringVar(value='Noch kein Download gestartet. Nicht importierte Regionen haben keine flächige Datenabdeckung.')
        ttk.Label(frame,textvariable=self.progress,wraplength=730).pack(anchor='w',pady=8)
        self.cancel_button=ttk.Button(frame,text='Import abbrechen',command=self.cancel,state='disabled');self.cancel_button.pack(anchor='w')
        ttk.Label(frame,text='Quellen: GeoNames (CC BY 4.0), OpenStreetMap-Mitwirkende (ODbL), optionale Wikidata-Identitäten (CC0). Keine Registrierung. Zusatzmerkmale können fehlen oder veraltet sein.',wraplength=730).pack(anchor='w',pady=8)
        self.window.protocol('WM_DELETE_WINDOW',self.close);self.refresh();self.window.after(150,self.poll)

    def choose_countries(self):
        window=tk.Toplevel(self.window);window.title('Europäische Länder und Gebiete auswählen');window.geometry('530x520')
        ttk.Label(window,text='Mehrere Länder wählen (⌘/Strg oder Umschalt).').pack(anchor='w',padx=12,pady=8)
        entries=sorted(COUNTRIES.items(),key=lambda row:row[1])
        frame=ttk.Frame(window);frame.pack(fill='both',expand=True,padx=12)
        choices=tk.Listbox(frame,selectmode='extended',exportselection=False)
        scrollbar=ttk.Scrollbar(frame,command=choices.yview);choices.configure(yscrollcommand=scrollbar.set)
        choices.pack(side='left',fill='both',expand=True);scrollbar.pack(side='right',fill='y')
        chosen={c.strip().upper() for c in self.countries.get().split(',')}
        for index,(code,name) in enumerate(entries):
            choices.insert('end',name+' ('+code+')')
            if code in chosen:choices.selection_set(index)
        buttons=ttk.Frame(window);buttons.pack(fill='x',padx=12,pady=10)
        ttk.Button(buttons,text='Alle',command=lambda:choices.selection_set(0,'end')).pack(side='left')
        ttk.Button(buttons,text='Keine',command=lambda:choices.selection_clear(0,'end')).pack(side='left',padx=6)
        def apply():self.countries.set(', '.join(entries[i][0] for i in choices.curselection()));window.destroy()
        ttk.Button(buttons,text='Auswahl übernehmen',command=apply).pack(side='right')

    def refresh(self):
        rows=self.app.inventory.coverage();text=[]
        for row in rows:
            label=row.get('name') or row.get('country')
            if row['key'].startswith('osm:'):label=row['key'][4:].rsplit(':',1)[0]
            text.append(label+': '+str(row.get('kinds',{}).get('settlement',row['count']))+' '+('Aufenthaltsorte' if row['key'].startswith('geonames:') else 'OSM-Merkmale')+' · '+('teilweise kartiert, keine Vollerhebung' if row['key'].startswith('osm:') else 'importiert')+' · Stand '+row['updated_at'])
        if not rows:text=['Noch keine Länder importiert. Der mitgelieferte kleine Reiseführerkatalog bleibt nutzbar.']
        for name in REGIONS:
            if not any(r['key'].startswith('osm:'+name+':') for r in rows):text.append(name+': regionale Zusatzmerkmale noch nicht importiert')
        imported={r.get('country') for r in rows if r['key'].startswith('geonames:')}
        text.append('Fehlender Ortsbestand: '+(', '.join(COUNTRIES[c] for c in COUNTRIES if c not in imported) or 'keiner im definierten Suchraum'))
        for attempt in self.app.inventory.attempts():
            if attempt['status']!='success':text.append(attempt['key']+': '+{'failed':'Quelle nicht erreichbar / Import fehlgeschlagen','cancelled':'abgebrochen'}.get(attempt['status'],attempt['status'])+' · '+attempt['error'])
        folder=self.app.inventory.path.parent/'destination-downloads'
        size=self.app.inventory.path.stat().st_size
        raw=sum(p.stat().st_size for p in folder.glob('*') if p.is_file()) if folder.exists() else 0
        text.append(f'Zieldatenbank {size/1048576:.1f} MiB · wiederverwendbare Downloads {raw/1048576:.1f} MiB')
        text.append('Freizeitdaten: kartierte Angebote, räumlich und nach Kategorien teilweise untersucht; keine Vollerhebung. Nicht untersucht ist kein negatives Ergebnis. Ruhe und tatsächliche Wege sind ungeprüft.')
        self.coverage.configure(state='normal');self.coverage.delete('1.0','end');self.coverage.insert('end','\n'.join(text));self.coverage.configure(state='disabled')

    def run(self,work):
        if self.context:return
        context=SearchContext(seconds=7200,budget=100);self.context=context;self.app.import_context=context
        self.import_button.configure(state='disabled');self.region_button.configure(state='disabled');self.cancel_button.configure(state='normal');self.app.search_button.configure(state='disabled')
        self.extract_button.configure(state='disabled')
        def emit(kind,value):self.events.put((kind,value))
        def worker():
            try:work(DestinationImportService(self.app.inventory),context,emit)
            except (OSError,ValueError,InterruptedError,KeyError) as exc:emit('phase',str(exc))
            except Exception as exc:emit('phase','Importfehler: '+str(exc)+'. Alter Stand bleibt nutzbar.')
            finally:
                emit('phase','Lokalen Suchindex aufbauen; bisherige Reisedaten bleiben unverändert.')
                try:
                    if not context.cancel.is_set():emit('catalog',DestinationCatalog(self.app.inventory,context))
                except Exception as exc:emit('phase','Datenstand konnte nicht geladen werden: '+str(exc))
                emit('done',None)
        thread=threading.Thread(target=worker,name='destination-import',daemon=False);self.app.workers.append(thread);thread.start()

    def import_countries(self,refresh=False):
        codes=[c.strip().upper() for c in self.countries.get().split(',') if c.strip()]
        if not codes or any(c not in COUNTRIES for c in codes):
            messagebox.showerror('Länder wählen','Unterstützte Codes: '+', '.join(COUNTRIES),parent=self.window);return
        self.run(lambda service,ctx,emit:service.import_countries(codes,ctx,emit,refresh=refresh))

    def update_region(self):
        try:
            if self.bounds.get().strip():
                bounds=tuple(float(x.strip()) for x in self.bounds.get().split(','));name=self.region_name.get().strip()
                if len(bounds)!=4 or not name:raise ValueError()
            else:name=self.region.get();bounds=REGIONS[name]
        except (KeyError,ValueError):
            messagebox.showerror('Region prüfen','Name und vier Koordinaten angeben oder eine vorhandene Region wählen.',parent=self.window);return
        def work(service,ctx,emit):
            service.update_region(name,bounds,ctx,emit,force=True)
            # Bounded exact identities; optional failure does not discard OSM data.
            features=service.inventory.nearby((bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2,60,'features')
            try:service.enrich_wikidata([f['tags'].get('wikidata','') for f in features],ctx,emit)
            except (OSError,ValueError) as exc:emit('phase','OSM nutzbar; Wikidata-Ergänzung nicht erreichbar: '+str(exc))
        self.run(work)

    def poll(self):
        if not self.window.winfo_exists():return
        while True:
            try:kind,value=self.events.get_nowait()
            except queue.Empty:break
            if kind=='phase':self.progress.set(value)
            elif kind=='catalog':
                self.app.catalog=value
                total=sum(r.get('kinds',{}).get('settlement',0) for r in self.app.inventory.coverage())
                self.app.status.set(f'Zieldaten bereit: {total:,} importierte Orte · {len(value.destinations):,} räumliche Vertreter in der Vorauswahl.')
                if hasattr(self.app.provider,'catalog'):self.app.provider.catalog=value
            elif kind=='done':
                self.context=None;self.app.import_context=None;self.refresh()
                self.import_button.configure(state='normal');self.region_button.configure(state='normal');self.cancel_button.configure(state='disabled');self.app.search_button.configure(state='normal')
                self.extract_button.configure(state='normal')
                if self.close_requested:self.window.destroy();return
        self.window.after(150,self.poll)

    def cancel(self):
        if self.context:self.context.cancel.set();self.progress.set('Import wird abgebrochen. Erfolgreich abgeschlossene Länder bleiben nutzbar.')

    def import_extract(self):
        name=self.region.get()
        self.run(lambda service,ctx,emit:service.import_extract(name,ctx,emit))

    def import_local(self):
        path=filedialog.askopenfilename(parent=self.window,filetypes=[('OSM PBF','*.pbf')])
        if not path:return
        try:name,bounds=self.selected_bounds()
        except ValueError as exc:messagebox.showerror('Ausschnitt prüfen',str(exc),parent=self.window);return
        self.run(lambda service,ctx,emit:service.import_pbf(path,name,bounds,ctx,emit))

    def selected_bounds(self):
        if self.bounds.get().strip():
            try:bounds=tuple(float(x.strip()) for x in self.bounds.get().split(','))
            except ValueError:raise ValueError('Vier Koordinaten Süd, West, Nord, Ost angeben.') from None
            name=self.region_name.get().strip()
            if len(bounds)!=4 or not name:raise ValueError('Ausschnittname und vier Koordinaten angeben.')
            return name,bounds
        name=self.region.get();return name,REGIONS[name]

    def fill_search_area(self):
        try:
            request=self.app.read_request()
            pool=self.app.catalog.candidates(request)
            unknown=[p for p in pool if p.get('feature_profile',{}).get('coverage')=='unknown']
            if not unknown:
                self.progress.set('Keine ununtersuchten Ortsumfelder in der Vorauswahl. Regionale Kartierung kann dennoch unvollständig sein.');return
            # Three separated local tiles, never an implicit whole-country download.
            from ...core.planning.PlaceResearch import distance
            selected=[]
            for p in unknown:
                if all(distance(p,old)>35 for old in selected):selected.append(p)
                if len(selected)==3:break
            def work(service,ctx,emit):
                for p in selected:
                    lat,lon=p['latitude'],p['longitude']
                    service.update_region('Umgebung '+p['name'],(lat-.08,lon-.1,lat+.08,lon+.1),ctx,emit)
            self.run(work)
        except ValueError as exc:messagebox.showerror('Suchgebiet prüfen',str(exc),parent=self.window)

    def close(self):
        if self.context:self.close_requested=True;self.cancel();self.window.withdraw()
        else:self.window.destroy()
