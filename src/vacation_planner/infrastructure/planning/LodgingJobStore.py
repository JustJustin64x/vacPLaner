"""Durable working research, separate from explicitly saved travel snapshots.

A token rejects late checkpoints from a superseded run. Fingerprints bind every
checkpoint to its destination, dates, guests and criteria. No network operations.
"""
import copy
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from ...core.planning.LodgingResearch import query_key,initialize,finish,summarize
from .TripStore import timestamp


class LodgingJobStore:
    def __init__(self,trip_store):
        self.path=Path(trip_store.path).with_name(Path(trip_store.path).stem+'-research.sqlite3')
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS lodging_jobs (id TEXT PRIMARY KEY, query_key TEXT NOT NULL, trip_id TEXT NOT NULL, token TEXT NOT NULL, state TEXT NOT NULL, payload TEXT NOT NULL, updated_at TEXT NOT NULL)')
            columns={r[1] for r in db.execute('PRAGMA table_info(lodging_jobs)')}
            if 'summary' not in columns:db.execute("ALTER TABLE lodging_jobs ADD COLUMN summary TEXT NOT NULL DEFAULT '{}'")

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=5)
        try:
            with db:yield db
        finally:db.close()

    @staticmethod
    def _selection(previous,current):
        for field,index in (('lodgings','selected_lodging'),('transports','selected_transport')):
            old=previous.get(field,[]);new=current.get(field,[]);selected=previous.get(index,0)
            if not 0<=selected<len(old):continue
            identity=old[selected].get('id') if field=='lodgings' else old[selected].get('mode')
            if identity is None:continue
            matches=[i for i,x in enumerate(new) if (x.get('id') if field=='lodgings' else x.get('mode'))==identity]
            if len(matches)==1:current[index]=matches[0]

    @staticmethod
    def summary(trip):
        return dict(destination=trip['destination']['name'],start=trip['start'],end=trip['end'],
            adults=trip['request']['adults'],children_ages=trip['request'].get('children_ages',[]),rooms=trip['request']['rooms'],
            metrics=summarize(trip.get('lodging_research',{})))

    def begin(self,trip):
        trip=copy.deepcopy(trip);initialize(trip);key=query_key(trip);token=str(uuid4())
        import hashlib
        identity=hashlib.sha256((trip['id']+'|'+key).encode()).hexdigest()
        with self.connect() as db:
            db.execute('INSERT INTO lodging_jobs (id,query_key,trip_id,token,state,payload,updated_at,summary) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET token=excluded.token,state=excluded.state,payload=excluded.payload,updated_at=excluded.updated_at,summary=excluded.summary',
                       (identity,key,trip['id'],token,'running',json.dumps(trip,ensure_ascii=False,allow_nan=False),timestamp(),json.dumps(self.summary(trip),ensure_ascii=False)))
        return identity,token,key

    def checkpoint(self,handle,trip,state='running'):
        identity,token,key=handle
        if state not in ('running','paused','finished','error'):raise ValueError('Unbekannter Recherchejobstatus')
        if query_key(trip)!=key:raise ValueError('Recherchefortschritt gehört zu anderen Reiseparametern')
        with self.connect() as db:
            # Hold the transaction across read/merge/write: a UI selection must
            # survive a checkpoint without replacing newer research evidence.
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT payload FROM lodging_jobs WHERE id=? AND token=?',(identity,token)).fetchone()
            if row is None:return False
            current=copy.deepcopy(trip);self._selection(json.loads(row[0]),current)
            db.execute('UPDATE lodging_jobs SET payload=?,state=?,updated_at=?,summary=? WHERE id=? AND token=?',
                       (json.dumps(current,ensure_ascii=False,allow_nan=False),state,timestamp(),json.dumps(self.summary(current),ensure_ascii=False),identity,token))
        return True

    def remember_selection(self,trip):
        key=query_key(trip)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows=db.execute('SELECT id,payload FROM lodging_jobs WHERE trip_id=? AND query_key=?',(trip['id'],key)).fetchall()
            for identity,payload in rows:
                current=json.loads(payload);self._selection(trip,current)
                db.execute('UPDATE lodging_jobs SET payload=? WHERE id=?',(json.dumps(current,ensure_ascii=False,allow_nan=False),identity))

    def list(self):
        with self.connect() as db:
            # Backfill only old progress records once. Ordinary refreshes read
            # compact metadata, not every property's evidence/HTML excerpts.
            for identity,payload in db.execute("SELECT id,payload FROM lodging_jobs WHERE summary='{}'").fetchall():
                db.execute('UPDATE lodging_jobs SET summary=? WHERE id=?',(json.dumps(self.summary(json.loads(payload)),ensure_ascii=False),identity))
            rows=db.execute('SELECT id,state,summary,updated_at FROM lodging_jobs ORDER BY updated_at DESC').fetchall()
        return [dict(json.loads(summary),id=identity,state=state,updated_at=updated) for identity,state,summary,updated in rows]

    def load(self,identity):
        with self.connect() as db:row=db.execute('SELECT query_key,payload FROM lodging_jobs WHERE id=?',(identity,)).fetchone()
        if row is None:raise KeyError('Recherchefortschritt nicht gefunden')
        trip=json.loads(row[1])
        if query_key(trip)!=row[0]:raise ValueError('Gespeicherter Recherchebezug ist widersprüchlich')
        for e in trip.get('lodging_research',{}).get('entries',[]):
            if e['state']=='running':finish(e,'cancelled','Vorheriger Prozess während Prüfung beendet; gezielte Fortsetzung möglich')
        from ...core.planning.TravelOffers import expire_offers
        return expire_offers(trip)

    def delete(self,identity):
        with self.connect() as db:db.execute('DELETE FROM lodging_jobs WHERE id=?',(identity,))
