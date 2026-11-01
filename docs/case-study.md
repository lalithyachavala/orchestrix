# Case Study — Orchestrix: AI Agent & Workflow Orchestration

> **Independent illustrative engineering demonstration.** Original portfolio
> artifact. Not affiliated with any real company or product. All business data
> is synthetic.

## 1. Problem

Teams want AI agents to *do* work — look a customer up, check an order, open a
ticket, update the CRM, notify someone — not just chat about it. Three things
make that hard to ship responsibly:

1. **Genuine tool use.** The agent must pick the right tool and arguments from
   the task and intermediate results, then act on real systems. Hardcoded
   scripts don't generalize.
2. **Safety.** Some actions (CRM writes, outbound messages) must not fire
   unattended. A human has to approve before they execute.
3. **Observability & recovery.** Operators need to see each tool call's input
   and output live, and recover cleanly when one fails.

Orchestrix is a working platform that addresses all three with a single
vendor-neutral runtime.

## 2. Agent orchestration

The centerpiece is one real **reason → act → observe** loop (`agents/runtime.py`):

```
build PlanContext(task, instructions, tool schemas, history)
→ adapter.decide() → Decision(tool+args | finish)
→ [gate if sensitive] → dispatch tool on live data → record observation
→ repeat until finish or step budget
```

The loop is decoupled from reasoning by the **`AgentAdapter`** interface
(`agents/adapter.py`). The shipped default, **`MockPlanner`**, is deterministic
and **keyless** — the entire platform runs and demos with zero API keys. It is
not canned output: on every step it reads the task, the agent's available tool
**schemas**, and the actual observations returned so far, then routes to the
next tool and derives arguments from that state (e.g. it resolves a customer by
searching, then reuses the returned `customer_id` to open a ticket). Swapping
`ADAPTER=claude` routes the identical loop through a real LLM's tool-use API;
nothing else changes. Real adapters are intentionally not bundled or keyed.

**Multi-agent (experimental).** A supervisor (`agents/supervisor.py`)
decomposes one task into `research → analysis → execution` and routes each
phase to a specialized agent with a restricted toolset. Each sub-agent is a
first-class `Execution` through the same runtime, so every phase is
independently inspectable. Approval is auto-granted across the chain for the
demo and labelled as such; single-agent runs keep real human approval.

## 3. Tool schemas

Each tool is a typed definition (`tools/registry.py`): a name, a description, a
**JSON Schema** for its parameters, a handler that runs against the seeded
SQLite datastore, and a `sensitive` flag.

```python
ToolDef(
  name="create_ticket",
  description="Open a support ticket for a customer.",
  parameters={"type":"object",
    "properties":{"customer_id":{...},"subject":{"type":"string"},
                  "priority":{"enum":["low","normal","high","urgent"]}},
    "required":["customer_id","subject"]},
  handler=create_ticket,          # inserts a real row, returns the record
  sensitive=False)
```

The six tools: `search_customers`, `get_order`, `create_ticket` (read/write),
`update_crm` **(sensitive)**, `send_notification` **(sensitive)**,
`generate_report`. The schemas are what the adapter is handed as the agent's
affordances — the same shape a real LLM tool-use request expects — so the mock
and a real model consume an identical contract. Arguments are validated in the
handler (`_require`, enum coercion, id normalization); bad input raises
`ToolError`, which the runtime treats as a genuine, recoverable failure.

## 4. Permissions & human-in-the-loop

Permissions are **declarative and centrally enforced**, not sprinkled through
handlers:

- A tool marked `sensitive=True` cannot execute until approved.
- When the loop selects a sensitive tool, it records the intended call
  (tool + chosen args) as a `pending_approval` step, flips the execution to
  `pending_approval`, emits an SSE event, and **suspends** — the handler is
  never invoked.
- The operator sees exactly what will run and the agent's stated rationale,
  then calls `/approve` or `/reject`.
  - **Approve** → the runtime executes that step, then resumes planning.
  - **Reject** → the step is marked `rejected`, recorded as a declined action,
    and the loop continues (the planner treats it as handled, so it won't loop).

An agent is also scoped to a **subset of tools** at creation; it can only ever
call what it was granted. This is a two-layer model: *which tools an agent may
use* (configuration) and *which calls need a human* (per-tool sensitivity).

## 5. State management

An `Execution` is a persisted, ordered list of typed `ExecutionStep`s plus a
status (`queued → running → pending_approval → completed | failed`). Because
the full step history is the state:

- A run **pauses and resumes** across an approval with no special machinery —
  `resume()` just finds the trailing `pending_approval` step and continues.
- The planner is **stateless between steps**; it re-derives its next move from
  the persisted history each turn, which keeps it deterministic and
  restart-safe.
- State lives in SQLite (`store.py`), so runs survive an API reload mid-demo.

Live state reaches the UI over **Server-Sent Events**. Each state change is
pushed to a per-execution async queue; the SSE endpoint sends a snapshot first
(so late subscribers are correct) then streams deltas until a terminal event.

## 6. Error handling

- **Tool failures** raise `ToolError` (missing record, bad id, missing arg).
  The runtime retries up to 2× with the attempt count recorded on the step,
  then marks the step `failed` and the execution `failed`.
- **Recovery** is explicit: the monitor surfaces a Retry control that re-drives
  the failed step and, on success, continues the run.
- **Boundaries** are validated by Pydantic at the API edge; typed HTTP errors
  (404/409) guard illegal transitions (e.g. approving a run that isn't waiting).
- **SSE robustness**: the stream falls back to polling the persisted status on
  timeout, so the terminal state is never missed even if an event races.

## 7. Scalability & security notes

- Stateless API → horizontal scale; pipeline stages (classify / act / notify)
  can become queue-fed workers behind the same adapter contract.
- Secrets (if a real adapter is enabled) stay server-side via env; the mock
  default means no secret is required to run or demo.
- PII: synthetic data only. In production the datastore is where field-level
  encryption, redaction, and retention controls would attach.

## 8. Honest limitations

- The default planner is deterministic heuristics over tool schemas and state
  — a genuine tool-calling *architecture*, but not a learned model. Real
  reasoning is opt-in behind the adapter.
- SQLite + an in-memory SSE queue is single-node; production would use Postgres
  and a shared broker (Redis/NATS) for multi-worker streaming.
- Auth is out of scope for the demo (no IdP/session layer).
- Approval in the multi-agent demo is auto-granted (clearly labelled
  experimental); only single-agent runs exercise real human approval.
- Dev dependency note: the pinned Next.js has an upstream advisory; this is a
  local, non-deployed demo. Bump before any real deployment.
