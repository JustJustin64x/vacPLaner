"""Read-only view of the existing price workflow, no separate research worker."""
import tkinter as tk
from tkinter import ttk
import webbrowser
from ...core.planning.LodgingResearch import LABELS,summarize


class LodgingResearchWindow:
    def __init__(self,app,trip):
        self.app=app;self.trip_id=trip['id'];self.entries={}
        self.window=tk.Toplevel(app.root);self.window.title('Unterkunftsprüfliste · '+trip['destination']['name'])
        self.window.geometry('1000x650');self.window.minsize(750,450)
        self.summary=ttk.Label(self.window,wraplength=950,justify='left',padding=12);self.summary.pack(fill='x')
        frame=ttk.Frame(self.window);frame.pack(fill='both',expand=True,padx=12)
        self.tree=ttk.Treeview(frame,columns=('name','state','system'),show='headings',selectmode='browse',height=10)
        for k,label,w in [('name','Unterkunft',260),('state','Prüfstand',340),('system','System / Variante',250)]:
            self.tree.heading(k,text=label);self.tree.column(k,width=w,minwidth=100)
        scroll=ttk.Scrollbar(frame,orient='vertical',command=self.tree.yview);self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.tree.pack(fill='both',expand=True)
        self.detail=tk.Text(self.window,height=9,wrap='word',state='disabled');self.detail.pack(fill='x',padx=12,pady=8)
        actions=ttk.Frame(self.window,padding=12);actions.pack(fill='x')
        ttk.Button(actions,text='Verzeichniseintrag öffnen',command=self.open_source).pack(side='left')
        ttk.Button(actions,text='Schließen',command=self.window.destroy).pack(side='right')
        self.tree.bind('<<TreeviewSelect>>',lambda e:self.show_entry())
        self.refresh(trip)

    def refresh(self,trip):
        if not self.window.winfo_exists() or trip['id']!=self.trip_id:return
        ledger=trip.get('lodging_research',{});self.entries={e['id']:e for e in ledger.get('entries',[])}
        m=summarize(ledger) if ledger else {'found':0,'official_websites':0,'offer_checks':0,'source_quotes':0,'confirmed_properties':0,'states':{}}
        self.summary.configure(text=f"{trip['destination']['name']}: {m['found']} gefunden · {m['official_websites']} Websites zugeordnet · {m['offer_checks']} Angebotsversuche · {m['source_quotes']} Quellenquoten · {m['confirmed_properties']} vollständig bestätigt\n"+
            ' · '.join(LABELS.get(k,k)+': '+str(v) for k,v in m['states'].items())+'\nKeine vollständige Markt-/Preisabdeckung. Nicht geprüft bedeutet nicht ausgebucht. Fortsetzung über die vorhandene Preisaktion.')
        selected=self.tree.selection()
        for e in self.entries.values():
            values=(e['lodging']['name'],LABELS.get(e['state'],e['state']),e.get('system','')+' / '+e.get('variant',''))
            if self.tree.exists(e['id']):self.tree.item(e['id'],values=values)
            else:self.tree.insert('','end',iid=e['id'],values=values)
        for identity in self.tree.get_children():
            if identity not in self.entries:self.tree.delete(identity)
        if selected and self.tree.exists(selected[0]):self.tree.selection_set(selected[0])
        elif self.tree.get_children():self.tree.selection_set(self.tree.get_children()[0])
        self.show_entry()

    def show_entry(self):
        selected=self.tree.selection();e=self.entries.get(selected[0]) if selected else None
        lines=[]
        if e:
            lines=[e['lodging']['name'],LABELS.get(e['state'],e['state'])+': '+e['reason'],
                'Adresse: '+e['lodging'].get('address','unbekannt'),
                f"Bearbeitungen: {e['attempts']} · HTTP: {e['network_calls']}",
                'Verzeichnis: '+e['lodging'].get('source',''),
                'Website-Hinweis: '+e['lodging'].get('url','')]
            if e.get('booking_url'):lines.append('Beobachtete Buchungsquelle: '+e['booking_url'])
            if e.get('identity_source'):lines.append('Zusätzlicher Identitätsbeleg: '+e['identity_source'])
            for rejected in e.get('rejected_responses',[]):
                lines.append('Nicht angenommen: '+rejected['reason']+' · '+rejected['source']+' · '+rejected['at'])
            for o in e.get('offers',[]):
                lines.append('Quellenquote '+o['original_amount']+' '+o['original_currency']+' · Abruf '+o['retrieved_at'])
                for fee in o.get('details',{}).get('included_surcharges',[]):lines.append('Im Quellenbetrag enthalten: '+fee['label']+' '+fee['amount']+' '+o['original_currency'])
                from ...core.planning.OfferPresentation import lodging_evidence_lines
                lines+=lodging_evidence_lines(o)
                for room in o.get('details',{}).get('selected_rooms',[]):
                    lines.append(str(room['quantity'])+' × '+room['name']+' · Tarif '+(room.get('tariff_name') or 'nicht veröffentlicht'))
                    if room.get('source_terms'):lines.append('Quellenbedingungen: '+room['source_terms'])
                lines+=o.get('unresolved',[])
        self.detail.configure(state='normal');self.detail.delete('1.0','end');self.detail.insert('end','\n'.join(lines));self.detail.configure(state='disabled')

    def open_source(self):
        selected=self.tree.selection();e=self.entries.get(selected[0]) if selected else None
        if e:
            from ...infrastructure.planning.LodgingSourcePolicy import normalize
            try:url=normalize(e['lodging']['source'])
            except ValueError:return
            webbrowser.open(url)
