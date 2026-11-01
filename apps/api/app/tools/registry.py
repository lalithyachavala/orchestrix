"""Tool layer. Each tool is a typed schema + a handler that runs against the
seeded datastore for real. `sensitive=True` means the runtime gates the call
behind human approval before it executes.

A tool raises ToolError on bad input / missing records — that is a genuine
failure the runtime surfaces, retries, and lets a human re-drive.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from .. import db


class ToolError(Exception):
    pass


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any]          # JSON Schema (type object)
    handler: Callable[[dict], Any]
    sensitive: bool = False

    def schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "sensitive": self.sensitive,
            "parameters": self.parameters,
        }


def _require(args: dict, key: str) -> Any:
    if key not in args or args[key] in (None, ""):
        raise ToolError(f"missing required argument: {key}")
    return args[key]


def _cust_row(cid: str) -> dict:
    r = db.one("SELECT * FROM customers WHERE id=?", (cid,))
    if not r:
        raise ToolError(f"customer not found: {cid}")
    return dict(r)


# ---- handlers -----------------------------------------------------------

def search_customers(args: dict) -> Any:
    query = str(_require(args, "query")).strip().lower()
    limit = int(args.get("limit", 5))
    rows = db.q("SELECT * FROM customers")
    hits = [
        dict(r) for r in rows
        if query in r["name"].lower()
        or query in r["email"].lower()
        or query in r["region"].lower()
        or query in r["tier"].lower()
        or query in r["id"].lower()
    ]
    return {"query": query, "count": len(hits), "results": hits[:limit]}


def get_order(args: dict) -> Any:
    oid = str(_require(args, "order_id")).upper().strip()
    if not oid.startswith("ORD-"):
        oid = "ORD-" + re.sub(r"\D", "", oid)
    r = db.one("SELECT * FROM orders WHERE id=?", (oid,))
    if not r:
        raise ToolError(f"order not found: {oid}")
    o = dict(r)
    o["items"] = json.loads(o["items"])
    o["customer"] = _cust_row(o["customer_id"])["name"]
    return o


def create_ticket(args: dict) -> Any:
    cid = str(_require(args, "customer_id"))
    _cust_row(cid)
    subject = str(_require(args, "subject"))[:200]
    priority = str(args.get("priority", "normal")).lower()
    if priority not in ("low", "normal", "high", "urgent"):
        priority = "normal"
    n = len(db.q("SELECT 1 FROM tickets")) + 9001
    tid = f"TCK-{n}"
    db.write(
        "INSERT INTO tickets VALUES (?,?,?,?,?,?)",
        (tid, cid, subject, priority, "open", "2025-11-01"),
    )
    return {"id": tid, "customer_id": cid, "subject": subject,
            "priority": priority, "status": "open"}


def update_crm(args: dict) -> Any:                 # sensitive: mutates CRM
    cid = str(_require(args, "customer_id"))
    _cust_row(cid)
    cur = db.one("SELECT * FROM crm_records WHERE customer_id=?", (cid,))
    stage = str(args.get("stage") or (cur["stage"] if cur else "new"))
    notes = str(args.get("notes") or (cur["notes"] if cur else ""))
    if cur:
        db.write("UPDATE crm_records SET stage=?, notes=?, updated_at=? WHERE customer_id=?",
                 (stage, notes, "2025-11-01", cid))
    else:
        db.write("INSERT INTO crm_records VALUES (?,?,?,?,?)",
                 (cid, stage, notes, "unassigned", "2025-11-01"))
    return {"customer_id": cid, "stage": stage, "notes": notes, "updated_at": "2025-11-01"}


def send_notification(args: dict) -> Any:          # sensitive: outbound action
    channel = str(args.get("channel", "email")).lower()
    recipient = str(_require(args, "recipient"))
    message = str(_require(args, "message"))[:500]
    n = len(db.q("SELECT 1 FROM notifications")) + 1
    nid = f"NOTE-{n:04d}"
    db.write("INSERT INTO notifications VALUES (?,?,?,?,?)",
             (nid, channel, recipient, message, "2025-11-01"))
    return {"id": nid, "channel": channel, "recipient": recipient,
            "message": message, "delivered": True}


def generate_report(args: dict) -> Any:
    kind = str(args.get("kind", "orders_summary")).lower()
    if kind not in ("orders_summary", "ticket_backlog", "customer_value"):
        kind = "orders_summary"
    if kind == "orders_summary":
        rows = db.q("SELECT status, COUNT(*) c, SUM(total) t FROM orders GROUP BY status")
        return {"kind": kind, "by_status": {r["status"]: {"orders": r["c"], "revenue": r["t"]} for r in rows}}
    if kind == "ticket_backlog":
        rows = db.q("SELECT priority, COUNT(*) c FROM tickets WHERE status='open' GROUP BY priority")
        return {"kind": kind, "open_by_priority": {r["priority"]: r["c"] for r in rows}}
    rows = db.q("SELECT name, tier, lifetime_value FROM customers ORDER BY lifetime_value DESC")
    return {"kind": kind, "customers": [dict(r) for r in rows]}


# ---- registry -----------------------------------------------------------

_P = {  # reusable JSON-schema fragments
    "query": {"type": "string", "description": "name, email, region, tier, or id substring"},
    "order_id": {"type": "string", "description": "e.g. ORD-5001"},
    "customer_id": {"type": "string", "description": "e.g. CUST-1001"},
}

REGISTRY: dict[str, ToolDef] = {
    "search_customers": ToolDef(
        "search_customers", "Find customer records matching a query.",
        {"type": "object", "properties": {"query": _P["query"],
         "limit": {"type": "integer", "default": 5}}, "required": ["query"]},
        search_customers),
    "get_order": ToolDef(
        "get_order", "Retrieve an order and its line items by id.",
        {"type": "object", "properties": {"order_id": _P["order_id"]},
         "required": ["order_id"]},
        get_order),
    "create_ticket": ToolDef(
        "create_ticket", "Open a support ticket for a customer.",
        {"type": "object", "properties": {"customer_id": _P["customer_id"],
         "subject": {"type": "string"},
         "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"]}},
         "required": ["customer_id", "subject"]},
        create_ticket),
    "update_crm": ToolDef(
        "update_crm", "Update a customer's CRM stage and notes.",
        {"type": "object", "properties": {"customer_id": _P["customer_id"],
         "stage": {"type": "string"}, "notes": {"type": "string"}},
         "required": ["customer_id"]},
        update_crm, sensitive=True),
    "send_notification": ToolDef(
        "send_notification", "Send an outbound notification to a recipient.",
        {"type": "object", "properties": {
         "channel": {"type": "string", "enum": ["email", "sms", "slack"]},
         "recipient": {"type": "string"}, "message": {"type": "string"}},
         "required": ["recipient", "message"]},
        send_notification, sensitive=True),
    "generate_report": ToolDef(
        "generate_report", "Generate an aggregate business report.",
        {"type": "object", "properties": {"kind": {"type": "string",
         "enum": ["orders_summary", "ticket_backlog", "customer_value"]}},
         "required": []},
        generate_report),
}


def schemas(names: list[str]) -> list[dict]:
    return [REGISTRY[n].schema() for n in names if n in REGISTRY]


def all_schemas() -> list[dict]:
    return [t.schema() for t in REGISTRY.values()]
