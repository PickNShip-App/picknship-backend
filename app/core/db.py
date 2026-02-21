import sqlite3
import threading
from datetime import datetime
from typing import Optional, List, Dict
import json

DB_PATH = "/var/data/picknship.db"
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
            name TEXT,
            access_token TEXT,
            installed_at TEXT,
            shipping_created INTEGER DEFAULT 0,
            domain TEXT,
            email TEXT
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            store_id TEXT,
            customer_name TEXT,
            customer_email TEXT,
            customer_phone TEXT,
            total REAL,
            currency TEXT,
            status TEXT,
            shipping_method TEXT,
            shipping_option TEXT,
            shipping_address TEXT,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(order_id, store_id)
        )
        """)
        conn.commit()
        conn.close()

def save_store(store_id: str, access_token: str, store: Dict, shipping_created: bool = False):
    with _lock:
        conn = _connect()
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute("""
        INSERT INTO stores (store_id, name, access_token, installed_at, shipping_created, domain, email)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(store_id) DO UPDATE SET
          access_token = excluded.access_token,
          name = excluded.name,
          installed_at = excluded.installed_at,
          shipping_created = excluded.shipping_created,
          domain = excluded.domain,
          email = excluded.email
        """, (
            str(store_id),
            store.get("name", ""),
            access_token,
            now,
            int(shipping_created),
            store.get("domain", ""),
            store.get("email", "")
        ))
        conn.commit()
        conn.close()

def save_store(store_id: str, access_token: str, store: Dict, shipping_created: bool = False) -> bool:
    """
    Guarda o actualiza una tienda.
    Devuelve True si es una tienda NUEVA, False si ya existía.
    """
    with _lock:
        conn = _connect()
        c = conn.cursor()

        c.execute("SELECT 1 FROM stores WHERE store_id = ?", (str(store_id),))
        existed = c.fetchone() is not None

        now = datetime.now().isoformat()

        c.execute("""
        INSERT INTO stores (store_id, name, access_token, installed_at, shipping_created, domain, email)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(store_id) DO UPDATE SET
          access_token = excluded.access_token,
          name = excluded.name,
          installed_at = excluded.installed_at,
          shipping_created = excluded.shipping_created,
          domain = excluded.domain,
          email = excluded.email
        """, (
            str(store_id),
            store.get("name", ""),
            access_token,
            now,
            int(shipping_created),
            store.get("domain", ""),
            store.get("email", "")
        ))

        conn.commit()
        conn.close()

        return not existed

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
    c.execute("""
    SELECT store_id, name, access_token, installed_at, shipping_created, domain, email
    FROM stores WHERE store_id = ?
    """, (str(store_id),))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "store_id": row[0],
        "name": row[1],
        "access_token": row[2],
        "installed_at": row[3],
        "shipping_created": bool(row[4]),
        "domain": row[5],
        "email": row[6]
    }

def list_stores() -> List[Dict]:
    conn = _connect()
    c = conn.cursor()
    c.execute("""
    SELECT store_id, name, domain, email, access_token, installed_at, shipping_created
    FROM stores ORDER BY installed_at DESC
    """)
    rows = c.fetchall()
    conn.close()
    return [
        {
            "store_id": r[0],
            "name": r[1],
            "domain": r[2],
            "email": r[3],     
            "access_token": r[4],
            "installed_at": r[5],
            "shipping_created": bool(r[6])
        } for r in rows
    ]

def save_order_if_new(order_data: dict) -> bool:
    """
    Save PickNShip order idempotently.
    Returns True if it was a new order, False if already existed.
    """
    with _lock:
        conn = _connect()
        c = conn.cursor()
        now = datetime.now().isoformat()

        order_id = str(order_data["order_id"])
        store_id = str(order_data["store_id"])

        shipping_address = json.dumps(order_data.get("shipping_address", {}))

        try:
            c.execute("""
            INSERT INTO orders (
                order_id, store_id, customer_name, customer_email, customer_phone,
                total, currency, status, shipping_method, shipping_option, shipping_address,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                store_id,
                order_data.get("customer_name", ""),
                order_data.get("customer_email", ""),
                order_data.get("customer_phone", ""),
                float(order_data.get("total", 0.0)),
                order_data.get("currency", "ARS"),
                order_data.get("status", ""),
                order_data.get("shipping_method", ""),
                order_data.get("shipping_option", ""),
                shipping_address,
                order_data.get("created_at", now),
                order_data.get("updated_at", now)
            ))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            c.execute("""
            UPDATE orders SET
                customer_name = ?,
                customer_email = ?,
                customer_phone = ?,
                total = ?,
                currency = ?,
                status = ?,
                shipping_method = ?,
                shipping_option = ?,
                shipping_address = ?,
                updated_at = ?
            WHERE order_id = ? AND store_id = ?
            """, (
                order_data.get("customer_name", ""),
                order_data.get("customer_email", ""),
                order_data.get("customer_phone", ""),
                float(order_data.get("total", 0.0)),
                order_data.get("currency", "ARS"),
                order_data.get("status", ""),
                order_data.get("shipping_method", ""),
                order_data.get("shipping_option", ""),
                shipping_address,
                order_data.get("updated_at", now),
                order_id,
                store_id
            ))
            conn.commit()
            conn.close()
            return False
        

def get_order(order_id: str, store_id: str) -> dict:
    conn = _connect()
    c = conn.cursor()
    c.execute("""
        SELECT customer_name, customer_email, customer_phone, total, currency, status,
               shipping_method, shipping_option, shipping_address, created_at, updated_at
        FROM orders WHERE order_id = ? AND store_id = ?
    """, (str(order_id), str(store_id)))
    row = c.fetchone()
    conn.close()
    if not row:
        return {}
    
    return {
        "customer_name": row[0],
        "customer_email": row[1],
        "customer_phone": row[2],
        "total": row[3],
        "currency": row[4],
        "status": row[5],
        "shipping_method": row[6],
        "shipping_option": row[7],
        "shipping_address": json.loads(row[8]) if row[8] else {},
        "created_at": row[9],
        "updated_at": row[10],
    }


def list_orders() -> List[Dict]:
    conn = _connect()
    c = conn.cursor()
    c.execute("""
        SELECT order_id, store_id, customer_name, total, currency,
               status, shipping_method, shipping_option,
               shipping_address, created_at, updated_at
        FROM orders
        ORDER BY created_at DESC
        LIMIT 100
    """)
    rows = c.fetchall()
    conn.close()

    return [
        {
            "order_id": r[0],
            "store_id": r[1],
            "customer_name": r[2],
            "total": r[3],
            "currency": r[4],
            "status": r[5],
            "shipping_method": r[6],
            "shipping_option": r[7],
            "shipping_address": r[8],
            "created_at": r[9],
            "updated_at": r[10],
        }
        for r in rows
    ]