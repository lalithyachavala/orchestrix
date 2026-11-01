"""Orchestrix API. FastAPI + the agent runtime. Keyless by default.

Boundaries validated by Pydantic; sensitive tool calls gated by the runtime;
live execution state streamed over SSE.
"""
from __future__ import annotations

import asyncio
import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from . import db, store
from .agents import supervisor
from .agents.runtime import runtime
from .models import AgentCreate, MultiAgentRequest, RunRequest
from .tools.registry import all_schemas

app = FastAPI(title="Orchestrix API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    # allow any localhost port — the demo may run on a non-default port if 3000
    # is taken. Override with WEB_ORIGIN for a fixed deployment.
    allow_origin_regex=r"http://localhost:\d+",
    allow_origins=[os.getenv("WEB_ORIGIN", "http://localhost:3000")],
    allow_methods=["*"], allow_headers=["*"],
)

_tasks: set[asyncio.Task] = set()        # keep background task refs alive


def _spawn(coro) -> None:
    t = asyncio.create_task(coro)
    _tasks.add(t)
    t.add_done_callback(_tasks.discard)


DEFAULT_AGENTS = [
    AgentCreate(name="Support Resolver",
                instructions="Resolve inbound customer issues. Look up the customer, inspect any "
                "referenced order, open a support ticket, and notify the customer. Escalate with "
                "urgent priority when an SLA is mentioned.",
                tools=["search_customers", "get_order", "create_ticket", "send_notification"]),
    AgentCreate(name="Account Manager",
                instructions="Keep CRM records accurate and customers informed. Look up the "
                "account, review orders, update the CRM stage, and send a follow-up.",
                tools=["search_customers", "get_order", "update_crm", "send_notification", "generate_report"]),
    AgentCreate(name="Ops Analyst",
                instructions="Answer operational questions with live reports over orders, tickets, "
                "and customer value.",
                tools=["generate_report", "search_customers"]),
]


def _ensure_default_agents() -> None:
    if not store.list_agents():
        for a in DEFAULT_AGENTS:
            store.create_agent(a)


@app.on_event("startup")
def _startup() -> None:
    db.init_and_seed()
    _ensure_default_agents()


@app.post("/admin/reset")
def admin_reset():
    """Reset the public demo back to seed data + default agents."""
    db.reset()
    _ensure_default_agents()
    return {"ok": True, "agents": len(store.list_agents())}


@app.get("/health")
def health():
    return {"ok": True, "adapter": runtime.adapter.name}


@app.get("/tools")
def tools():
    return {"tools": all_schemas()}


# ---- agents -------------------------------------------------------------

@app.post("/agents")
def create_agent(body: AgentCreate):
    return store.create_agent(body)


@app.get("/agents")
def list_agents():
    return store.list_agents()


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    a = store.get_agent(agent_id)
    if not a:
        raise HTTPException(404, "agent not found")
    return a


# ---- executions ---------------------------------------------------------

@app.post("/executions")
async def run_execution(body: RunRequest):
    agent = store.get_agent(body.agent_id)
    if not agent:
        raise HTTPException(404, "agent not found")
    ex = store.create_execution(agent, body.task)
    runtime.queue(ex.id)                 # create queue before SSE can subscribe
    _spawn(runtime.start(ex.id))
    return ex


@app.get("/executions")
def list_executions():
    return store.list_executions()


@app.get("/executions/{exec_id}")
def get_execution(exec_id: str):
    ex = store.get_execution(exec_id)
    if not ex:
        raise HTTPException(404, "execution not found")
    return ex


@app.post("/executions/{exec_id}/approve")
async def approve(exec_id: str):
    ex = store.get_execution(exec_id)
    if not ex:
        raise HTTPException(404, "execution not found")
    if ex.status != "pending_approval":
        raise HTTPException(409, "execution is not awaiting approval")
    _spawn(runtime.resume(exec_id, approved=True))
    return {"ok": True}


@app.post("/executions/{exec_id}/reject")
async def reject(exec_id: str):
    ex = store.get_execution(exec_id)
    if not ex:
        raise HTTPException(404, "execution not found")
    if ex.status != "pending_approval":
        raise HTTPException(409, "execution is not awaiting approval")
    _spawn(runtime.resume(exec_id, approved=False))
    return {"ok": True}


@app.post("/executions/{exec_id}/retry")
async def retry(exec_id: str):
    ex = store.get_execution(exec_id)
    if not ex:
        raise HTTPException(404, "execution not found")
    if ex.status != "failed":
        raise HTTPException(409, "execution has not failed")
    _spawn(runtime.retry(exec_id))
    return {"ok": True}


@app.get("/executions/{exec_id}/stream")
async def stream(exec_id: str):
    if not store.get_execution(exec_id):
        raise HTTPException(404, "execution not found")

    async def gen():
        ex = store.get_execution(exec_id)
        snap = {"type": "snapshot", "status": ex.status,
                "terminal": ex.status in ("completed", "failed", "pending_approval"),
                "steps": [s.model_dump() for s in ex.steps], "summary": ex.summary}
        yield {"data": json.dumps(snap)}
        if snap["terminal"]:
            return
        q = runtime.queue(exec_id)
        while True:
            try:
                evt = await asyncio.wait_for(q.get(), timeout=1.0)
            except asyncio.TimeoutError:
                cur = store.get_execution(exec_id)
                if cur.status in ("completed", "failed", "pending_approval"):
                    yield {"data": json.dumps(
                        {"type": "snapshot", "status": cur.status, "terminal": True,
                         "steps": [s.model_dump() for s in cur.steps], "summary": cur.summary})}
                    return
                continue
            yield {"data": json.dumps(evt)}
            if evt.get("terminal"):
                return

    return EventSourceResponse(gen())


# ---- multi-agent (experimental) ----------------------------------------

@app.post("/multi-agent/run")
async def multi_agent(body: MultiAgentRequest):
    return await supervisor.run(body.task)
