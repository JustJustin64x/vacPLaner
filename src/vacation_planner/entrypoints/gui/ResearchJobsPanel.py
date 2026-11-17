"""Resume durable working research without modifying saved travel snapshots."""
from tkinter import ttk,messagebox
from ...infrastructure.planning.LodgingJobStore import LodgingJobStore
from ...core.planning.RankingService import RankingService


class ResearchJobsPanel:
    def __init__(self,app):
        self.app=app;self.store=LodgingJobStore(app.store)
        self.frame=ttk.Frame(app.output_tabs,padding=12);app.output_tabs.add(self.frame,text='Recherchefortschritt')
        ttk.Label(self.frame,text='Unterkunftsrecherchen werden lokal als Arbeitsstände fortgeführt. Diese sind getrennt von „Gespeicherte Reisen“. Erst „Reise speichern“ bewahrt einen Reise-Snapshot. Öffnen startet keinen Internetabruf.',wraplength=820).pack(fill='x',pady=(0,12))
        self.tree=ttk.Treeview(self.frame,columns=('target','period','group','state'),show='headings',selectmode='browse')
        for key,label,width in [('target','Reiseziel',160),('period','Zeitraum',180),('group','Gruppe / Zimmer',180),('state','Fortschritt',260)]:
            self.tree.heading(key,text=label);self.tree.column(key,width=width,minwidth=90)
        bar=ttk.Scrollbar(self.frame,orient='vertical',command=self.tree.yview);bar.pack(side='right',fill='y');self.tree.configure(yscrollcommand=bar.set);self.tree.pack(fill='both',expand=True)
        actions=ttk.Frame(self.frame,padding=(0,10));actions.pack(fill='x')
        for label,command in [('Aktualisieren',self.refresh),('Arbeitsstand öffnen',self.open),('Öffnen und Unterkünfte fortsetzen',lambda:self.open(resume=True)),('Arbeitsstand löschen',self.delete)]:
            ttk.Button(actions,text=label,command=command).pack(anchor='w',pady=3)
        app.output_tabs.bind('<<NotebookTabChanged>>',self.tab_changed,add='+');self.refresh()

    def tab_changed(self,event=None):
        if self.app.output_tabs.select()==str(self.frame):self.refresh()

    def refresh(self):
        selected=self.tree.selection();self.tree.delete(*self.tree.get_children())
        for row in self.store.list():
            m=row['metrics'];left=sum(m['states'].get(k,0) for k in ('pending','running','cancelled','deferred_budget','source_error'))
            state={'running':'Letzter Lauf begonnen','paused':'Fortsetzbar','finished':'Begrenzt abgeschlossen','error':'Fehler'}.get(row['state'],row['state'])
            group=f"{row['adults']} Erwachsene"+(f" + {len(row['children_ages'])} Kinder" if row['children_ages'] else '')+f" / {row['rooms']} Zimmer"
            self.tree.insert('','end',iid=row['id'],values=(row['destination'],row['start']+' – '+row['end'],group,f"{state} · {m['found']} Funde · {left} weiter prüfbar · {m['source_quotes']} Quoten"))
        if selected and self.tree.exists(selected[0]):self.tree.selection_set(selected[0])

    def open(self,resume=False):
        selected=self.tree.selection()
        if not selected:return
        app=self.app
        if app.running or app.price_context:app.cancel_search()
        else:app.generation+=1
        app.cancel_enrichment()
        try:trip=self.store.load(selected[0]);RankingService.recompute(trip)
        except (KeyError,ValueError,OSError) as exc:messagebox.showerror('Recherchefortschritt',str(exc),parent=app.root);return
        app.trips[trip['id']]=trip;app.update_row(trip)
        tree=app.idea_tree if trip.get('filter_status')=='offen' else app.tree
        tree.selection_set(trip['id']);app.select_trip(tree=tree);app.saved_id=None
        app.populate_request(trip['request']);app.output_tabs.select(0)
        app.status.set('Recherche-Arbeitsstand geöffnet; Quellenzeitpunkte erhalten. Gespeicherte Reisen unverändert. Fortsetzen prüft offene und veraltete Schritte.')
        if resume:app.research_prices(lodging_continue=True)

    def delete(self):
        selected=self.tree.selection()
        if selected and messagebox.askyesno('Arbeitsstand löschen','Nur diesen Recherche-Arbeitsstand löschen? Gespeicherte Reisen bleiben erhalten.',parent=self.app.root):
            self.store.delete(selected[0]);self.refresh()
