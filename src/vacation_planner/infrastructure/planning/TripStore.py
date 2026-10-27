from __future__ import annotations
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class TripStore:
    """Short-lived connections keep UI and worker independent; versioned JSON snapshots."""
    def __init__(self, path=None):
        self.path = Path(path or os.environ.get('VACATION_PLANNER_DB',
                         str(Path.home()/'Library/Application Support/Urlaubsplaner/trips.sqlite3')))
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version > 1:
                raise ValueError('Diese Datenbank benötigt eine neuere Programmversion.')
            db.execute('PRAGMA journal_mode=WAL')
            if version == 0:
                db.execute('CREATE TABLE IF NOT EXISTS trips (id TEXT PRIMARY KEY, name TEXT NOT NULL, payload TEXT NOT NULL, saved_at TEXT NOT NULL)')
                db.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, payload TEXT NOT NULL, fetched_at TEXT NOT NULL)')
                db.execute('PRAGMA user_version=1')

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(str(self.path), timeout=5)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def save(self, name, trip, identifier=None):
        if not name.strip():
            raise ValueError('Bitte einen Namen für die Reise eingeben.')
        identifier = identifier or str(uuid4())
        payload = dict(schema_version=1, trip=trip)
        with self.connect() as db:
            db.execute('INSERT INTO trips VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,payload=excluded.payload,saved_at=excluded.saved_at',
                       (identifier,name.strip(),json.dumps(payload,ensure_ascii=False,allow_nan=False),timestamp()))
        return identifier

    def list(self):
        with self.connect() as db:
            return [dict(id=r[0],name=r[1],saved_at=r[2]) for r in db.execute('SELECT id,name,saved_at FROM trips ORDER BY saved_at DESC')]

    def load(self, identifier):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM trips WHERE id=?',(identifier,)).fetchone()
        if row is None:
            raise KeyError('Gespeicherte Reise nicht gefunden')
        payload = json.loads(row[0])
        if payload['schema_version'] != 1:
            raise ValueError('Unbekanntes Reiseformat')
        return payload['trip']

    def delete(self, identifier):
        with self.connect() as db:
            db.execute('DELETE FROM trips WHERE id=?',(identifier,))

    def duplicate(self, identifier, name):
        trip = self.load(identifier)
        trip['id'] = str(uuid4())
        trip['saved_name'] = name
        return self.save(name,trip)

    def cache_get(self, key, max_age=None):
        with self.connect() as db:
            row = db.execute('SELECT payload,fetched_at FROM cache WHERE key=?',(key,)).fetchone()
        if row is None:
            return None
        age = (datetime.now(timezone.utc)-datetime.fromisoformat(row[1])).total_seconds()
        if max_age is not None and age > max_age:
            return None
        return json.loads(row[0]),row[1]

    def cache_set(self, key, payload, fetched_at):
        with self.connect() as db:
            db.execute('INSERT INTO cache VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET payload=excluded.payload,fetched_at=excluded.fetched_at',
                       (key,json.dumps(payload,ensure_ascii=False),fetched_at))
