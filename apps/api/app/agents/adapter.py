"""The seam that decouples the runtime from any reasoning backend.

The runtime hands an adapter the task, the agent instructions, the available
tool SCHEMAS, and the step history so far. The adapter returns the next
Decision: call a tool (with args IT chose) or finish. Swapping mock -> a real
LLM changes only this layer; the loop, tools, approval, and UI are untouched.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Protocol


@dataclass
class PlanContext:
    task: str
    instructions: str
    tools: list[dict]                       # tool schemas the agent may use
    history: list[dict]                     # prior steps: {tool,args,observation,status}


@dataclass
class Decision:
    action: Literal["tool", "finish"]
    thought: str                            # stated rationale (shown in UI)
    tool: Optional[str] = None
    args: dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None           # when action == finish


class AgentAdapter(Protocol):
    name: str
    def decide(self, ctx: PlanContext) -> Decision: ...


def get_adapter(kind: str = "mock") -> AgentAdapter:
    kind = (kind or "mock").lower()
    if kind == "mock":
        from .mock_planner import MockPlanner
        return MockPlanner()
    # Real adapters are opt-in. They are intentionally NOT bundled or keyed.
    # A ClaudeAdapter / OpenAIAdapter would implement `decide` by sending the
    # same PlanContext (tools as the provider's tool-use schema) and mapping
    # the model's tool_use / stop back to a Decision. Drop one in here.
    raise RuntimeError(
        f"adapter '{kind}' not installed. Default is keyless 'mock'. "
        f"Add an adapter impl + key to enable a real LLM."
    )
