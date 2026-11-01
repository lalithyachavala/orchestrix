"""Deterministic, keyless planner — the default reasoning backend.

It is NOT a canned script. On every step it reads the task, the agent's
available tool schemas, and the REAL observations returned so far, then decides
the next tool call (choosing arguments from that state) or finishes. Same loop
shape a real LLM tool-use adapter would drive; swap it in behind AgentAdapter.

Reproducible by construction (no randomness) so screenshots/demos are stable.
"""
from __future__ import annotations

import re

from .. import db
from .adapter import AgentAdapter, Decision, PlanContext

# intent -> the tool that satisfies it, in execution order (gather -> act -> notify)
PLAN = [
    ("customer_lookup", "search_customers"),
    ("order_lookup", "get_order"),
    ("report", "generate_report"),
    ("ticket", "create_ticket"),
    ("crm_update", "update_crm"),
    ("notify", "send_notification"),
]

_KEYWORDS = {
    "customer_lookup": ("customer", "account", "client", "look up", "lookup", "find", "who is"),
    "order_lookup": ("order", "shipment", "delivery", "ord-"),
    "report": ("report", "summary", "summarize", "analytics", "how many", "overview", "backlog", "revenue"),
    "ticket": ("ticket", "issue", "complaint", "support", "problem", "bug", "escalat"),
    "crm_update": ("crm", "update", "stage", "mark as", "pipeline", "note", "at risk", "renewal", "expansion"),
    "notify": ("notify", "email", "send", "alert", "inform", "message them", "let them know", "reach out"),
}


class MockPlanner(AgentAdapter):
    name = "mock"

    def decide(self, ctx: PlanContext) -> Decision:
        task = ctx.task
        low = task.lower()
        have = {t["name"] for t in ctx.tools}
        done = _satisfied_tools(ctx.history)
        cust = _customer_from_history(ctx.history) or _customer_from_task(task)

        for intent, tool in PLAN:
            if tool not in have or tool in done:
                continue
            if not _detected(intent, low, task):
                continue
            args = self._args(intent, tool, task, low, ctx, cust)
            if args is None:
                continue  # intent detected but not resolvable from current state → skip
            return Decision(action="tool", tool=tool, args=args,
                            thought=_thought(intent, tool, args, cust))

        return Decision(action="finish", thought="All resolvable sub-goals handled.",
                        summary=_summary(ctx.history))

    # ---- argument selection (reads task + observations) -----------------

    def _args(self, intent, tool, task, low, ctx, cust):
        if intent == "customer_lookup":
            q = _resolve_query(task)
            return {"query": q} if q else None

        if intent == "order_lookup":
            oid = _order_id(task)
            if not oid and cust:
                row = db.one("SELECT id FROM orders WHERE customer_id=? ORDER BY created_at DESC",
                             (cust["id"],))
                oid = row["id"] if row else None
            return {"order_id": oid} if oid else None

        if intent == "report":
            return {"kind": _report_kind(low)}

        if intent == "ticket":
            if not cust:
                return None
            return {"customer_id": cust["id"],
                    "subject": _ticket_subject(task),
                    "priority": _priority(low)}

        if intent == "crm_update":
            if not cust:
                return None
            args = {"customer_id": cust["id"], "notes": f"Agent action: {task[:160]}"}
            stage = _crm_stage(low)
            if stage:
                args["stage"] = stage
            return args

        if intent == "notify":
            if not cust:
                return None
            return {"channel": "email",
                    "recipient": cust.get("email") or cust["id"],
                    "message": _notify_message(task, ctx.history)}
        return None


# ---- state helpers ------------------------------------------------------

def _satisfied_tools(history) -> set[str]:
    # a tool counts as done if it succeeded OR a human rejected it (don't re-propose)
    return {h["tool"] for h in history if h.get("tool") and h.get("status") in ("success", "rejected")}


def _detected(intent, low, task) -> bool:
    if any(k in low for k in _KEYWORDS[intent]):
        return True
    if intent == "customer_lookup":
        # imply a lookup when an action needs a customer, or a known account is named
        if any(any(k in low for k in _KEYWORDS[i]) for i in ("ticket", "crm_update", "notify")):
            return True
        if _name_in_task(task):
            return True
    return False


def _name_in_task(task) -> bool:
    if re.search(r"[\w.+-]+@[\w.-]+\.\w+", task) or re.search(r"CUST-\d+", task, re.I):
        return True
    tl = task.lower()
    return any(r["name"].lower() in tl for r in db.q("SELECT name FROM customers"))


def _customer_from_history(history):
    for h in history:
        if h.get("tool") == "search_customers" and h.get("status") == "success":
            res = (h.get("observation") or {}).get("results") or []
            if res:
                return res[0]
    return None


def _customer_from_task(task):
    m = re.search(r"CUST-\d+", task, re.I)
    if not m:
        return None
    r = db.one("SELECT * FROM customers WHERE id=?", (m.group(0).upper(),))
    return dict(r) if r else None


# ---- extraction from natural-language task ------------------------------

def _resolve_query(task):
    m = re.search(r"[\w.+-]+@[\w.-]+\.\w+", task)
    if m:
        return m.group(0)
    m = re.search(r"CUST-\d+", task, re.I)
    if m:
        return m.group(0).upper()
    tl = task.lower()
    for r in db.q("SELECT name FROM customers"):
        if r["name"].lower() in tl:
            return r["name"]
    for kw in ("enterprise", "growth", "starter", "us-east", "us-west", "eu-west", "apac"):
        if kw in tl:
            return kw
    m = re.search(r"(?:customer|account|client|for)\s+([A-Z][\w&.\-]+(?:\s+[A-Z][\w&.\-]+)?)", task)
    return m.group(1) if m else None


def _order_id(task):
    m = re.search(r"ORD-?\s?(\d+)", task, re.I)
    return f"ORD-{m.group(1)}" if m else None


def _priority(low):
    if any(k in low for k in ("urgent", "asap", "critical", "immediately", "sla")):
        return "urgent"
    if "high" in low:
        return "high"
    if "low priority" in low or "minor" in low:
        return "low"
    return "normal"


def _crm_stage(low):
    for needle, stage in (("at risk", "at_risk"), ("at-risk", "at_risk"), ("churn", "churned"),
                          ("expansion", "expansion"), ("upsell", "expansion"),
                          ("renewal", "renewal"), ("onboard", "onboarding"),
                          ("closed won", "closed_won"), ("won", "closed_won")):
        if needle in low:
            return stage
    return None


def _report_kind(low):
    if "backlog" in low or "ticket" in low:
        return "ticket_backlog"
    if "value" in low or "revenue" in low or "ltv" in low or "lifetime" in low:
        return "customer_value"
    return "orders_summary"


def _ticket_subject(task):
    s = re.sub(r"\s+", " ", task).strip()
    return s[:120]


def _notify_message(task, history):
    done = []
    for h in history:
        if h.get("status") != "success":
            continue
        if h["tool"] == "create_ticket":
            done.append(f"ticket {h['observation'].get('id')} opened")
        elif h["tool"] == "update_crm":
            done.append(f"CRM stage set to {h['observation'].get('stage')}")
    tail = (" Actions taken: " + "; ".join(done) + ".") if done else ""
    return f"Re: {task[:100]}.{tail}"


def _thought(intent, tool, args, cust):
    who = f" for {cust['name']}" if cust else ""
    reasons = {
        "customer_lookup": f"Task references a customer; searching records with '{args.get('query')}' to resolve the account.",
        "order_lookup": f"Need order detail before acting; retrieving {args.get('order_id')} to inspect status.",
        "report": f"Task asks for insight; generating the '{args.get('kind')}' report from live data.",
        "ticket": f"Task describes an issue{who}; opening a '{args.get('priority')}' support ticket.",
        "crm_update": f"Task implies a CRM change{who}; updating stage/notes to keep the record accurate.",
        "notify": f"Work is done{who}; sending an outbound notification (sensitive — requires approval).",
    }
    return reasons.get(intent, f"Calling {tool}.")


def _summary(history):
    parts = []
    for h in history:
        if h.get("status") != "success":
            continue
        t, o = h["tool"], (h.get("observation") or {})
        if t == "search_customers":
            parts.append(f"matched {o.get('count', 0)} customer(s)")
        elif t == "get_order":
            parts.append(f"retrieved {o.get('id')} ({o.get('status')})")
        elif t == "generate_report":
            parts.append(f"generated {o.get('kind')} report")
        elif t == "create_ticket":
            parts.append(f"opened ticket {o.get('id')}")
        elif t == "update_crm":
            parts.append(f"updated CRM to '{o.get('stage')}'")
        elif t == "send_notification":
            parts.append(f"notified {o.get('recipient')}")
    rejected = [h["tool"] for h in history if h.get("status") == "rejected"]
    s = "Completed: " + ("; ".join(parts) if parts else "no actions required") + "."
    if rejected:
        s += f" Declined by human: {', '.join(rejected)}."
    return s
