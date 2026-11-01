# Orchestrix — 45-Second Walkthrough Script

Timed shot list + narration for the demo video/GIF. Ports shown assume the
local instance on **:3010** (web) / **:8010** (api); the documented defaults are
3000/8000 on a clean machine.

| Time | Screen | Action on camera | Narration (voiceover / caption) |
|------|--------|------------------|---------------------------------|
| 0:00–0:05 | **Overview** (`/`) | Land on dashboard; cursor sweeps the four stat tiles and the tool catalog. | "Orchestrix — a single plane for AI agents that actually *do* business work. Six tools, real executions." |
| 0:05–0:11 | **Agents** (`/agents`) | Click *Agents*. Show the Support Resolver: instructions + granted tools, two badged as approval-gated. | "Each agent has instructions and a scoped set of tools. Two are sensitive — they'll need a human." |
| 0:11–0:16 | Agents | Type the task: *"Cedar Health order ORD-5003 is delayed past SLA — open an urgent ticket and notify them."* Click **Run agent**. | "Give it a real task in plain language." |
| 0:16–0:27 | **Execution Monitor** (`/executions/[id]`) | Timeline streams live: `search_customers` → `get_order` → `create_ticket`, each showing input and the real output JSON + the agent's rationale. | "Genuine tool-calling: it resolves the customer, pulls the order, opens the ticket — every input and output streamed live over SSE." |
| 0:27–0:34 | Monitor | Run halts on a purple **approval** card for `send_notification`. Click **Approve**. Step executes; status flips to *completed* with a summary. | "Before the sensitive action fires, it stops for a human. Approve — and only now does it send." |
| 0:34–0:40 | **Workflow Builder** (`/workflows`) | Show the node graph: trigger → reasoning → tools → condition → approval gate → complete/error. Pan/zoom slightly. | "The same pipeline, visual — triggers, reasoning, tool nodes, branches, and approval gates you can edit." |
| 0:40–0:45 | **Multi-Agent** (`/multi-agent`) | Click *Run supervisor*. Three cards fill: research → analysis → execution, each completed with its tool trace. | "And an experimental supervisor that splits a task across specialized agents. That's Orchestrix." |

## Recording notes

- Window ≥ 1440px wide, dark OS theme, browser zoom 100%.
- Reset state for a clean demo: stop the API, delete `apps/api/orchestrix.db*`,
  restart — startup reseeds data and the three default agents.
- The approval pause is the money shot — let it sit ~1s before approving so the
  gate reads clearly.
- For a GIF, Claude-in-Chrome's `gif_creator` records the same flow; export with
  `download: true`.
