# Screenshots

Capture these six views (covers the 5–8 screenshot deliverable). Each is a
stop on the [walkthrough](../demo/walkthrough-script.md). Save as PNG into this
folder with the suggested filenames.

| File | View | What it shows |
|------|------|---------------|
| `01-overview.png` | Overview (`/`) | Stat tiles (agents, executions, tool calls), recent runs, the six-tool catalog with approval badges. |
| `02-agents.png` | Agents (`/agents`) | Agent config — instructions + scoped tools, sensitive tools flagged. |
| `03-execution-timeline.png` | Monitor (`/executions/[id]`) | Live tool-call timeline: each step's input, real output JSON, and the agent's rationale. |
| `04-approval-gate.png` | Monitor | The `pending_approval` card for `send_notification` with Approve / Reject. |
| `05-workflow-builder.png` | Workflow Builder (`/workflows`) | React Flow graph: trigger → reasoning → tools → condition → approval → complete/error. |
| `06-multi-agent.png` | Multi-Agent (`/multi-agent`) | Supervisor plan + research/analysis/execution child traces. |

All seven views were driven live and verified rendering during the build
session, and the end-to-end flow (Overview → Agents → run → live timeline →
approval gate → completion) is recorded in
[`../demo/walkthrough.gif`](../demo/walkthrough.gif).

## How to (re)capture individual PNGs

App running on `:3010` (or `:3000`). Use the browser's screenshot or OS capture
on each route above. (The automated screenshot tool in this environment doesn't
return a file path, so individual PNGs aren't pre-committed — the walkthrough
GIF is the committed visual artifact; grab stills from it or the live app.)
