"""Pydantic boundary models. Validation happens here, once, at every edge."""
from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

# ---- agents -------------------------------------------------------------

class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    instructions: str = Field(min_length=1, max_length=2000)
    tools: list[str] = Field(min_length=1)          # tool names the agent may call
    max_steps: int = Field(default=8, ge=1, le=20)


class Agent(AgentCreate):
    id: str
    created_at: str


# ---- tools --------------------------------------------------------------

class ToolSchema(BaseModel):
    name: str
    description: str
    sensitive: bool
    parameters: dict[str, Any]                       # JSON Schema


# ---- executions ---------------------------------------------------------

StepStatus = Literal["running", "success", "failed", "pending_approval", "rejected"]
ExecStatus = Literal["queued", "running", "pending_approval", "completed", "failed"]


class ExecutionStep(BaseModel):
    index: int
    kind: Literal["reason", "tool", "finish"]
    status: StepStatus
    tool: Optional[str] = None
    sensitive: bool = False
    args: dict[str, Any] = {}
    observation: Any = None
    error: Optional[str] = None
    attempts: int = 0
    thought: Optional[str] = None                    # adapter's stated rationale
    ts: str = ""


class RunRequest(BaseModel):
    agent_id: str
    task: str = Field(min_length=1, max_length=1000)


class Execution(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    task: str
    status: ExecStatus
    steps: list[ExecutionStep] = []
    summary: Optional[str] = None
    created_at: str
    updated_at: str


class MultiAgentRequest(BaseModel):
    task: str = Field(min_length=1, max_length=1000)
