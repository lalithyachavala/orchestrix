"""Persistence for platform state (agents, executions) in SQLite as JSON blobs.
Small surface, so no ORM. IDs are content-free counters + prefix."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from . import db
from .models import Agent, AgentCreate, Execution


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _id(prefix: str, table: str) -> str:
    n = len(db.q(f"SELECT 1 FROM {table}")) + 1
    return f"{prefix}-{n:04d}"


# ---- agents -------------------------------------------------------------

def create_agent(data: AgentCreate) -> Agent:
    agent = Agent(id=_id("AGT", "agents"), created_at=_now(), **data.model_dump())
    db.write("INSERT INTO agents VALUES (?,?)", (agent.id, agent.model_dump_json()))
    return agent


def list_agents() -> list[Agent]:
    return [Agent.model_validate_json(r["data"]) for r in db.q("SELECT data FROM agents")]


def get_agent(agent_id: str) -> Agent | None:
    r = db.one("SELECT data FROM agents WHERE id=?", (agent_id,))
    return Agent.model_validate_json(r["data"]) if r else None


# ---- executions ---------------------------------------------------------

def create_execution(agent: Agent, task: str) -> Execution:
    now = _now()
    ex = Execution(id=_id("EXE", "executions"), agent_id=agent.id, agent_name=agent.name,
                   task=task, status="queued", created_at=now, updated_at=now)
    db.write("INSERT INTO executions VALUES (?,?,?)", (ex.id, now, ex.model_dump_json()))
    return ex


def save_execution(ex: Execution) -> None:
    ex.updated_at = _now()
    db.write("UPDATE executions SET data=? WHERE id=?", (ex.model_dump_json(), ex.id))


def get_execution(exec_id: str) -> Execution | None:
    r = db.one("SELECT data FROM executions WHERE id=?", (exec_id,))
    return Execution.model_validate_json(r["data"]) if r else None


def list_executions(limit: int = 50) -> list[Execution]:
    rows = db.q("SELECT data FROM executions ORDER BY created_at DESC LIMIT ?", (limit,))
    return [Execution.model_validate_json(r["data"]) for r in rows]
