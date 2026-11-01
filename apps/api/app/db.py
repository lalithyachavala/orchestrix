"""SQLite datastore. Stdlib only — no ORM needed for a handful of tables.

Holds BOTH the synthetic business records (what tools query/mutate) and the
platform state (agents, executions). One file, created and seeded on import.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading

# Default to a file next to the app; override with ORCHESTRIX_DB to point at a
# mounted persistent disk in production (e.g. /data/orchestrix.db on Render).
DB_PATH = os.getenv("ORCHESTRIX_DB") or os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "orchestrix.db")

_lock = threading.Lock()          # ponytail: single global write lock; fine for a single-node demo
_conn: sqlite3.Connection | None = None


def conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
    return _conn


def q(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return conn().execute(sql, params).fetchall()


def one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    return conn().execute(sql, params).fetchone()


def write(sql: str, params: tuple = ()) -> None:
    with _lock:
        conn().execute(sql, params)
        conn().commit()


SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
  id TEXT PRIMARY KEY, name TEXT, email TEXT, tier TEXT, region TEXT,
  lifetime_value INTEGER, created_at TEXT
);
CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY, customer_id TEXT, status TEXT, total INTEGER,
  items TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS tickets (
  id TEXT PRIMARY KEY, customer_id TEXT, subject TEXT, priority TEXT,
  status TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS crm_records (
  customer_id TEXT PRIMARY KEY, stage TEXT, notes TEXT, owner TEXT, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS notifications (
  id TEXT PRIMARY KEY, channel TEXT, recipient TEXT, message TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS agents (
  id TEXT PRIMARY KEY, data TEXT
);
CREATE TABLE IF NOT EXISTS executions (
  id TEXT PRIMARY KEY, created_at TEXT, data TEXT
);
"""


def reset() -> None:
    """Wipe all tables and reseed business data. Platform state (agents,
    executions) is cleared too; the caller recreates default agents."""
    with _lock:
        for t in ("customers", "orders", "tickets", "crm_records",
                  "notifications", "agents", "executions"):
            conn().execute(f"DELETE FROM {t}")
        conn().commit()
    init_and_seed()          # customers now empty → reseeds business rows


def init_and_seed() -> None:
    c = conn()
    with _lock:
        c.executescript(SCHEMA)
        c.commit()
    if one("SELECT 1 FROM customers LIMIT 1"):
        return  # already seeded
    from .seed import CUSTOMERS, ORDERS, TICKETS, CRM
    with _lock:
        c.executemany(
            "INSERT INTO customers VALUES (?,?,?,?,?,?,?)",
            [(x["id"], x["name"], x["email"], x["tier"], x["region"],
              x["lifetime_value"], x["created_at"]) for x in CUSTOMERS],
        )
        c.executemany(
            "INSERT INTO orders VALUES (?,?,?,?,?,?)",
            [(x["id"], x["customer_id"], x["status"], x["total"],
              json.dumps(x["items"]), x["created_at"]) for x in ORDERS],
        )
        c.executemany(
            "INSERT INTO tickets VALUES (?,?,?,?,?,?)",
            [(x["id"], x["customer_id"], x["subject"], x["priority"],
              x["status"], x["created_at"]) for x in TICKETS],
        )
        c.executemany(
            "INSERT INTO crm_records VALUES (?,?,?,?,?)",
            [(x["customer_id"], x["stage"], x["notes"], x["owner"], x["updated_at"])
             for x in CRM],
        )
        c.commit()
