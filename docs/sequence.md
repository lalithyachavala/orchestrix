# Tool-Calling Sequence

How one task flows through the runtime, including a sensitive call gated by
human approval and the retry path on failure.

```mermaid
sequenceDiagram
  autonumber
  actor U as User
  participant W as Web (monitor)
  participant API as FastAPI
  participant RT as Runtime loop
  participant AD as Adapter (MockPlanner)
  participant TL as Tool + datastore

  U->>W: Run agent with task
  W->>API: POST /executions
  API->>RT: start(execution) [background]
  API-->>W: execution id
  W->>API: GET /executions/{id}/stream (SSE)

  loop until finish or step budget
    RT->>AD: decide(task, instructions, tool schemas, history)
    AD-->>RT: Decision(tool, args, thought)
    alt tool is sensitive
      RT->>API: step = pending_approval
      API-->>W: SSE: approval_required
      U->>W: Approve / Reject
      W->>API: POST /approve (or /reject)
      API->>RT: resume(approved)
    end
    RT->>TL: handler(args)
    alt success
      TL-->>RT: observation (live data)
      RT-->>W: SSE: step_done
    else ToolError
      TL-->>RT: raise
      RT->>TL: retry (≤2×)
      alt still failing
        RT->>API: status = failed
        API-->>W: SSE: step_failed
        U->>W: Retry
        W->>API: POST /retry
        API->>RT: retry()
      end
    end
  end

  RT-->>W: SSE: finish (summary, terminal)
```

## Decision contract

```python
@dataclass
class Decision:
    action: Literal["tool", "finish"]
    thought: str                    # rationale shown in the UI
    tool:   Optional[str] = None    # must be one of the agent's tools
    args:   dict = {}               # chosen from task + prior observations
    summary: Optional[str] = None   # when action == "finish"
```

The adapter only ever *names* a tool and arguments. The runtime owns
validation, approval, dispatch, retry, persistence, and streaming — so a real
LLM adapter inherits all of it for free.
