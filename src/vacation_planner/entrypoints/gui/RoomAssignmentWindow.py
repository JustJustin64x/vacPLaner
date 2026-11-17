"""Explicit room allocation editor; it neither researches nor books anything."""
import tkinter as tk
from tkinter import ttk,messagebox
from ...core.planning.RoomParty import room_parties,ages_from_text


class RoomAssignmentWindow:
    def __init__(self,parent,adults,ages,rooms,current,on_save):
        self.adults,self.ages,self.rooms,self.on_save=adults,ages,rooms,on_save
        self.window=tk.Toplevel(parent);self.window.title('Zimmeraufteilung');self.window.geometry('600x480');self.window.transient(parent)
        ttk.Label(self.window,text='Jede Person einmal zuordnen. Kinderalter in ganzen Jahren am Reisebeginn, mit Komma getrennt. Die Unterkunft muss diese Aufteilung anschließend bestätigen.',wraplength=560,padding=12).pack(fill='x')
        canvas=tk.Canvas(self.window,highlightthickness=0);scroll=ttk.Scrollbar(self.window,orient='vertical',command=canvas.yview)
        scroll.pack(side='right',fill='y');canvas.configure(yscrollcommand=scroll.set);canvas.pack(fill='both',expand=True)
        frame=ttk.Frame(canvas,padding=12);canvas.create_window((0,0),window=frame,anchor='nw')
        frame.bind('<Configure>',lambda _:canvas.configure(scrollregion=canvas.bbox('all')))
        for column,label in enumerate(('Zimmer','Erwachsene','Kinderalter')):ttk.Label(frame,text=label).grid(row=0,column=column,padx=10,pady=6)
        try:parties=room_parties(adults,ages,rooms,current)
        except ValueError:parties=room_parties(adults,ages,rooms)
        self.entries=[]
        for index,party in enumerate(parties,1):
            adult=tk.StringVar(value=str(party.adults));child=tk.StringVar(value=', '.join(map(str,party.children_ages)))
            ttk.Label(frame,text=str(index)).grid(row=index,column=0,padx=10,pady=4)
            ttk.Spinbox(frame,from_=0,to=40,textvariable=adult,width=8).grid(row=index,column=1,padx=10)
            ttk.Entry(frame,textvariable=child,width=28).grid(row=index,column=2,padx=10)
            self.entries.append((adult,child))
        actions=ttk.Frame(self.window,padding=12);actions.pack(fill='x')
        ttk.Button(actions,text='Übernehmen',command=self.save).pack(side='right')
        ttk.Button(actions,text='Abbrechen',command=self.window.destroy).pack(side='right',padx=8)

    def save(self):
        try:
            values=[{'adults':int(a.get()),'children_ages':ages_from_text(c.get())} for a,c in self.entries]
            parties=room_parties(self.adults,self.ages,self.rooms,values)
        except ValueError as exc:
            messagebox.showerror('Aufteilung prüfen',str(exc),parent=self.window);return
        self.on_save([p.to_dict() for p in parties]);self.window.destroy()
