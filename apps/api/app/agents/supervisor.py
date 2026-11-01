"""Experimental multi-agent demonstration.

A supervisor decomposes one task into research -> analysis -> execution phases
and routes each to a specialized agent. Each specialist is a normal agent run
through the SAME runtime, so every sub-run is a first-class, inspectable
Execution. Approval is auto-granted here (clearly experimental) so the chain
completes end-to-end; single-agent runs keep real human-in-the-loop approval.
"""
from __future__ import annotations

from .. import store
from ..models import AgentCreate
from .runtime import runtime

SPECIALISTS = {
    "research": ("Research Agent", "Gather the customer and order facts relevant to the task. "
                 "Do not take any write actions.", ["search_customers", "get_order"]),
    "analysis": ("Analysis Agent", "Turn the gathered facts into an aggregate report and a "
                 "recommendation.", ["generate_report"]),
    "execution": ("Execution Agent", "Carry out the resulting actions: open tickets, update CRM, "
                  "and notify stakeholders.", ["search_customers", "create_ticket",
                                               "update_crm", "send_notification"]),
}


def _ensure_specialist(role: str):
    name, instr, tools = SPECIALISTS[role]
    for a in store.list_agents():
        if a.name == name:
            return a
    return store.create_agent(AgentCreate(name=name, instructions=instr, tools=tools, max_steps=8))


def plan(task: str) -> list[dict]:
    return [
        {"role": "research", "objective": f"Resolve the accounts/orders behind: {task}",
         "tools": SPECIALISTS["research"][2]},
        {"role": "analysis", "objective": "Aggregate findings into a report + recommendation",
         "tools": SPECIALISTS["analysis"][2]},
        {"role": "execution", "objective": "Execute the resulting business actions",
         "tools": SPECIALISTS["execution"][2]},
    ]


async def run(task: str) -> dict:
    phases = plan(task)
    children: list[str] = []
    prior = ""
    for phase in phases:
        role = phase["role"]
        agent = _ensure_specialist(role)
        subtask = {
            "research": f"Research the accounts and orders relevant to: {task}",
            "analysis": f"Analyze and report on: {task}. Prior findings:{prior}",
            "execution": f"{task} Prior agent findings:{prior}",
        }[role]
        ex = store.create_execution(agent, subtask)
        runtime.queue(ex.id)
        await runtime.start(ex.id, auto_approve=True)   # experimental: auto-approved
        done = store.get_execution(ex.id)
        prior += f"\n[{role}:{agent.name}] {done.summary or 'done'}"
        children.append(ex.id)
    return {"task": task, "supervisor_plan": phases, "child_executions": children,
            "note": "Experimental multi-agent demo. Approval is auto-granted across the chain."}
