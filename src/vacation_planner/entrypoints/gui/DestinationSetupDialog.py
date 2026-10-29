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
        self.countries=tk.StringVar(value='AT, SI, HR')
        ttk.Label(frame,text='Europäische Länder als Codes, durch Kommas getrennt:').pack(anchor='w',pady=(10,0))
        ttk.Entry(frame,textvariable=self.countries).pack(fill='x')
        controls=ttk.Frame(frame);controls.pack(fill='x',pady=5)
        self.import_button=ttk.Button(controls,text='Länder herunterladen / aktualisieren',command=self.import_countries);self.import_button.pack(side='left')
        ttk.Button(controls,text='Alle unterstützten Länder auswählen',command=lambda:self.countries.set(', '.join(COUNTRIES))).pack(side='left',padx=6)
        self.region=ttk.Combobox(frame,state='readonly',values=list(REGIONS));self.region.current(0);self.region.pack(fill='x',pady=(10,3))
        ttk.Label(frame,text='Oder eigene Region: Name und Süd, West, Nord, Ost (Dezimalpunkt; höchstens 1 × 1 Grad).').pack(anchor='w')
        custom=ttk.Frame(frame);custom.pack(fill='x');self.region_name=tk.StringVar();self.bounds=tk.StringVar()
        ttk.Entry(custom,textvariable=self.region_name,width=24).pack(side='left');ttk.Entry(custom,textvariable=self.bounds).pack(side='left',fill='x',expand=True,padx=5)
        self.region_button=ttk.Button(frame,text='Regionale OSM-Merkmale aktualisieren',command=self.update_region);self.region_button.pack(anchor='w',pady=5)
        self.extract_button=ttk.Button(frame,text='Alternative: Regionalauszug laden (ca. 116–299 MB)',command=self.import_extract);self.extract_button.pack(anchor='w')
        ttk.Button(frame,text='Vorhandene regionale PBF-Datei verwenden',command=self.import_local).pack(anchor='w',pady=3)
        self.progress=tk.StringVar(value='Noch kein Download gestartet. Nicht importierte Regionen haben keine flächige Datenabdeckung.')
        ttk.Label(frame,textvariable=self.progress,wraplength=730).pack(anchor='w',pady=8)
        self.cancel_button=ttk.Button(frame,text='Import abbrechen',command=self.cancel,state='disabled');self.cancel_button.pack(anchor='w')
        ttk.Label(frame,text='Quellen: GeoNames (CC BY 4.0), OpenStreetMap-Mitwirkende (ODbL), optionale Wikidata-Identitäten (CC0). Keine Registrierung. Zusatzmerkmale können fehlen oder veraltet sein.',wraplength=730).pack(anchor='w',pady=8)
        self.window.protocol('WM_DELETE_WINDOW',self.close);self.refresh();self.window.after(150,self.poll)

    def refresh(self):
        rows=self.app.inventory.coverage();text=[]
        for row in rows:
            label=row.get('name') or row.get('country')
            if row['key'].startswith('osm:'):label=row['key'][4:].rsplit(':',1)[0]
            text.append(label+': '+str(row.get('kinds',{}).get('settlement',row['count']))+' '+('Aufenthaltsorte' if row['key'].startswith('geonames:') else 'OSM-Merkmale')+' · Stand '+row['updated_at'])
        if not rows:text=['Noch keine Länder importiert. Der mitgelieferte kleine Reiseführerkatalog bleibt nutzbar.']
        for name in REGIONS:
            if not any(r['key'].startswith('osm:'+name+':') for r in rows):text.append(name+': regionale Zusatzmerkmale noch nicht importiert')
        self.coverage.configure(state='normal');self.coverage.delete('1.0','end');self.coverage.insert('end','\n'.join(text));self.coverage.configure(state='disabled')

    def run(self,work):
        if self.context:return
        context=SearchContext(seconds=3600,budget=60);self.context=context;self.app.import_context=context
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

    def import_countries(self):
        codes=[c.strip().upper() for c in self.countries.get().split(',') if c.strip()]
        if not codes or any(c not in COUNTRIES for c in codes):
            messagebox.showerror('Länder wählen','Unterstützte Codes: '+', '.join(COUNTRIES),parent=self.window);return
        self.run(lambda service,ctx,emit:service.import_countries(codes,ctx,emit))

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
                self.app.status.set(f'Zieldaten bereit: {len(value.destinations)} Aufenthaltsorte. Gespeicherte Reisen bleiben unverändert.')
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
        name=self.region.get();bounds=REGIONS[name]
        self.run(lambda service,ctx,emit:service.import_pbf(path,name,bounds,ctx,emit))

    def close(self):
        if self.context:self.close_requested=True;self.cancel();self.window.withdraw()
        else:self.window.destroy()
