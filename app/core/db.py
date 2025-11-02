import sqlite3
import threading
from datetime import datetime
from typing import Optional, List, Dict

DB_PATH = "picknship.db"
_lock = threading.Lock()

def _connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with _lock:
        conn = _connect()
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT UNIQUE,
            store_name TEXT,
            access_token TEXT,
            installed_at TEXT,
            shipping_created INTEGER DEFAULT 0
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            store_id TEXT,
            payload TEXT,
            received_at TEXT
        )
        """)
        conn.commit()
        conn.close()

def save_store(store_id: str, access_token: str, store_name: Optional[str] = None, shipping_created: bool = False):
    with _lock:
        conn = _connect()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("""
        INSERT INTO stores (store_id, store_name, access_token, installed_at, shipping_created)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(store_id) DO UPDATE SET
          access_token = excluded.access_token,
          store_name = excluded.store_name,
          installed_at = excluded.installed_at,
          shipping_created = excluded.shipping_created
        """, (str(store_id), store_name or "", access_token, now, int(shipping_created)))
        conn.commit()
        conn.close()

def mark_shipping_created(store_id: str):
    with _lock:
        conn = _connect()
        c = conn.cursor()
        c.execute("UPDATE stores SET shipping_created = 1 WHERE store_id = ?", (str(store_id),))
        conn.commit()
        conn.close()

def get_store(store_id: str) -> Optional[Dict]:
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT store_id, store_name, access_token, installed_at, shipping_created FROM stores WHERE store_id = ?", (str(store_id),))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "store_id": row[0],
        "store_name": row[1],
        "access_token": row[2],
        "installed_at": row[3],
        "shipping_created": bool(row[4])
    }

def list_stores() -> List[Dict]:
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT store_id, store_name, access_token, installed_at, shipping_created FROM stores ORDER BY installed_at DESC")
    rows = c.fetchall()
    conn.close()
    return [
        {
            "store_id": r[0],
            "store_name": r[1],
            "access_token": r[2],
            "installed_at": r[3],
            "shipping_created": bool(r[4])
        } for r in rows
    ]

def save_order(order_id: str, store_id: str, payload: str):
    with _lock:
        conn = _connect()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("""
        INSERT INTO orders (order_id, store_id, payload, received_at)
        VALUES (?, ?, ?, ?)
        """, (str(order_id), str(store_id), payload, now))
        conn.commit()
        conn.close()
