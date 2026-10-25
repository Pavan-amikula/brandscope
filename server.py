"""Loopback-only demo API, SQLite persistence and static application server.

Deploy behind authentication before accepting private business data. The bundled
GitHub Pages version intentionally uses an explicitly labelled browser demo store.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlparse

from analytics import campaign

ROOT=Path(__file__).resolve().parent
DB=ROOT/'data/events.sqlite'


@contextmanager
def connect():
    db=sqlite3.connect(DB,timeout=10)
    db.row_factory=sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()


def init_db():
    DB.parent.mkdir(exist_ok=True)
    with connect() as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, timestamp TEXT, market TEXT, channel TEXT, amount_pence INTEGER, synthetic INTEGER)')
        db.execute('CREATE TABLE IF NOT EXISTS plans (id INTEGER PRIMARY KEY, timestamp TEXT, title TEXT, payload TEXT)')


def validate_event(obj):
    if not isinstance(obj,dict):raise ValueError('Expected an object')
    if not isinstance(obj.get('event_id'),str) or not re.fullmatch(r'[a-zA-Z0-9_-]{8,80}',obj['event_id']):
        raise ValueError('event_id must be 8–80 letters, numbers, underscores or hyphens')
    if obj.get('market') not in ['Sweden','Denmark','Norway','Finland','United Kingdom']:
        raise ValueError('Unsupported market')
    if obj.get('channel') not in ['CRM','Retail media','Paid social','Organic']:
        raise ValueError('Unsupported channel')
    amount=obj.get('amount_pence')
    if type(amount) is not int or not 0 < amount <= 10000000:
        raise ValueError('amount_pence must be a positive integer <= 10000000')
    if type(obj.get('synthetic')) is not bool:raise ValueError('Explicit synthetic boolean required')
    return obj


class Handler(SimpleHTTPRequestHandler):
    def send_json(self,obj,status=200):
        blob=json.dumps(obj,allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(blob)))
        self.end_headers();self.wfile.write(blob)

    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/health':return self.send_json(dict(status='ok',storage='SQLite',mode='local demo API'))
        if path=='/api/events':
            with connect() as db:
                events=[dict(r) for r in db.execute('SELECT * FROM events ORDER BY rowid DESC LIMIT 30')]
                totals=dict(db.execute('SELECT count(*) AS events, coalesce(sum(amount_pence),0) AS amount_pence, coalesce(sum(synthetic),0) AS synthetic_events FROM events').fetchone())
            return self.send_json(dict(events=events,totals=totals))
        if path=='/api/plans':
            with connect() as db:
                plans=[dict(r) for r in db.execute('SELECT * FROM plans ORDER BY id DESC LIMIT 20')]
            return self.send_json(plans)
        if path.startswith('/api/'):return self.send_json(dict(error='Not found'),404)
        return super().do_GET()

    def do_POST(self):
        # Prevent cross-site posts to a user's loopback service. Host binding and
        # host validation also reject DNS rebinding; no permissive CORS headers.
        if self.headers.get('Host') not in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']:
            return self.send_json(dict(error='Untrusted host'),403)
        origin=self.headers.get('Origin')
        if origin and origin not in [f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']:
            return self.send_json(dict(error='Cross-origin writes rejected'),403)
        if self.headers.get_content_type()!='application/json':return self.send_json(dict(error='JSON required'),415)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 16384:raise ValueError('Body must be 1–16384 bytes')
            obj=json.loads(self.rfile.read(length))
            path=urlparse(self.path).path
            if path=='/api/events':
                obj=validate_event(obj)
                with connect() as db:
                    cursor=db.execute('INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?)',
                        (obj['event_id'],datetime.now(timezone.utc).isoformat(),obj['market'],obj['channel'],obj['amount_pence'],int(obj['synthetic'])))
                    inserted=cursor.rowcount==1
                return self.send_json(dict(inserted=inserted,event_id=obj['event_id']),201 if inserted else 200)
            if path=='/api/campaign':
                return self.send_json(campaign(**obj))
            if path=='/api/plans':
                title=obj.get('title','') if isinstance(obj,dict) else ''
                if not isinstance(title,str) or not 1<=len(title)<=120:raise ValueError('title must be 1–120 characters')
                with connect() as db:
                    cursor=db.execute('INSERT INTO plans(timestamp,title,payload) VALUES (?,?,?)',
                        (datetime.now(timezone.utc).isoformat(),title,json.dumps(obj)))
                return self.send_json(dict(id=cursor.lastrowid,saved=True),201)
            return self.send_json(dict(error='Not found'),404)
        except (ValueError,TypeError,KeyError) as e:
            return self.send_json(dict(error=str(e)),400)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    init_db()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(ROOT/'web')))
    print(f'BrandScope: http://127.0.0.1:{args.port}',flush=True)
    server.serve_forever()
