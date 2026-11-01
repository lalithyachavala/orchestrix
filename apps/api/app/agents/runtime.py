"""The agent runtime: one real reason -> act -> observe loop.

- asks the adapter for the next Decision
- dispatches the chosen tool against live data, feeds the result back
- gates sensitive tools behind human approval (pauses the run)
- retries failed tool calls, then surfaces a failed state a human can re-drive
- streams every state change to an in-memory per-execution queue (-> SSE)

Pacing sleeps make the live timeline legible; they are not where the work is.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from .. import store
from ..models import Execution, ExecutionStep
from ..tools.registry import REGISTRY, ToolError, schemas
from .adapter import PlanContext, get_adapter

MAX_RETRIES = 2
STEP_PACING = 0.45          # seconds between planner steps (live-timeline feel)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Runtime:
    def __init__(self) -> None:
        self.adapter = get_adapter(os.getenv("ADAPTER", "mock"))
        self._queues: dict[str, asyncio.Queue] = {}
        self._auto: dict[str, bool] = {}     # auto-approve (multi-agent experimental demo)

    # ---- event plumbing ------------------------------------------------

    def queue(self, exec_id: str) -> asyncio.Queue:
        return self._queues.setdefault(exec_id, asyncio.Queue())

    async def _emit(self, ex: Execution, etype: str, **extra) -> None:
        terminal = ex.status in ("completed", "failed", "pending_approval")
        await self.queue(ex.id).put(
            {"type": etype, "status": ex.status, "terminal": terminal,
             "steps": [s.model_dump() for s in ex.steps],
             "summary": ex.summary, **extra})

    # ---- public entry points -------------------------------------------

    async def start(self, exec_id: str, auto_approve: bool = False) -> None:
        self._auto[exec_id] = auto_approve
        ex = store.get_execution(exec_id)
        agent = store.get_agent(ex.agent_id)
        ex.status = "running"
        store.save_execution(ex)
        await self._emit(ex, "status")
        await self._loop(ex, agent)

    async def resume(self, exec_id: str, approved: bool) -> None:
        ex = store.get_execution(exec_id)
        agent = store.get_agent(ex.agent_id)
        step = _trailing(ex, "pending_approval")
        if step is None:
            return
        if approved:
            await self._emit(ex, "approval", decision="approved", index=step.index)
            await self._execute(ex, step)
            if step.status == "failed":
                ex.status = "failed"
                store.save_execution(ex)
                await self._emit(ex, "status")
                return
        else:
            step.status = "rejected"
            step.observation = {"declined_by_human": True}
            await self._emit(ex, "approval", decision="rejected", index=step.index)
        ex.status = "running"
        store.save_execution(ex)
        await self._loop(ex, agent)

    async def retry(self, exec_id: str) -> None:
        ex = store.get_execution(exec_id)
        agent = store.get_agent(ex.agent_id)
        step = _trailing(ex, "failed")
        if step is None:
            return
        ex.status = "running"
        step.status = "running"
        store.save_execution(ex)
        await self._emit(ex, "retry", index=step.index)
        await self._execute(ex, step)
        if step.status == "failed":
            ex.status = "failed"
            store.save_execution(ex)
            await self._emit(ex, "status")
            return
        await self._loop(ex, agent)

    # ---- the loop ------------------------------------------------------

    async def _loop(self, ex: Execution, agent) -> None:
        while sum(1 for s in ex.steps if s.kind == "tool") < agent.max_steps:
            ctx = self._context(ex, agent)
            decision = self.adapter.decide(ctx)
            await asyncio.sleep(STEP_PACING)

            if decision.action == "finish":
                ex.steps.append(ExecutionStep(index=len(ex.steps), kind="finish",
                                              status="success", thought=decision.thought, ts=_now()))
                ex.status = "completed"
                ex.summary = decision.summary
                store.save_execution(ex)
                await self._emit(ex, "finish")
                return

            tool = REGISTRY[decision.tool]
            step = ExecutionStep(index=len(ex.steps), kind="tool", tool=tool.name,
                                 sensitive=tool.sensitive, args=decision.args,
                                 thought=decision.thought, status="running", ts=_now())
            ex.steps.append(step)
            await self._emit(ex, "step_start", index=step.index)

            if tool.sensitive and not self._auto.get(ex.id):
                step.status = "pending_approval"
                ex.status = "pending_approval"
                store.save_execution(ex)
                await self._emit(ex, "approval_required", index=step.index)
                return  # pause until resume()

            await self._execute(ex, step)
            if step.status == "failed":
                ex.status = "failed"
                store.save_execution(ex)
                await self._emit(ex, "status")
                return

        # step budget exhausted
        ex.status = "completed"
        ex.summary = (ex.summary or "") + " Step budget reached; stopping."
        store.save_execution(ex)
        await self._emit(ex, "finish")

    async def _execute(self, ex: Execution, step: ExecutionStep) -> None:
        tool = REGISTRY[step.tool]
        for attempt in range(1, MAX_RETRIES + 1):
            step.attempts = attempt
            step.status = "running"
            try:
                step.observation = tool.handler(step.args)
                step.error = None
                step.status = "success"
                store.save_execution(ex)
                await self._emit(ex, "step_done", index=step.index)
                return
            except ToolError as e:
                step.error = str(e)
                store.save_execution(ex)
                await self._emit(ex, "step_error", index=step.index,
                                 attempt=attempt, error=str(e))
                await asyncio.sleep(0.3)
        step.status = "failed"
        store.save_execution(ex)
        await self._emit(ex, "step_failed", index=step.index)

    def _context(self, ex: Execution, agent) -> PlanContext:
        history = [{"tool": s.tool, "args": s.args, "observation": s.observation,
                    "status": s.status}
                   for s in ex.steps if s.kind == "tool"]
        return PlanContext(task=ex.task, instructions=agent.instructions,
                           tools=schemas(agent.tools), history=history)


def _trailing(ex: Execution, status: str) -> ExecutionStep | None:
    for s in reversed(ex.steps):
        if s.status == status:
            return s
    return None


runtime = Runtime()
