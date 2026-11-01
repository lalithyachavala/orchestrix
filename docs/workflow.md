# Workflow Visualization

The **Workflow Builder** (`/workflows`) is a live React Flow editor: add nodes
from the palette, drag to arrange, drag between handles to connect, and press
**Run workflow** to execute the modelled pipeline as a real agent run.

Node types: **trigger**, **AI reasoning**, **tool execution**, **conditional
branch**, **approval**, **completion**, **error**.

The default graph models the Support Resolver pipeline:

```mermaid
flowchart TD
  T([Trigger: Inbound request]):::trig --> AI[AI Reasoning: classify & plan]:::ai
  AI --> C1[Tool: search_customers]:::tool
  C1 --> C2[Tool: get_order]:::tool
  C2 --> COND{Order delayed / SLA?}:::cond
  C2 -->|not found| ERR([Error: failed / retry]):::err
  COND -->|yes| TK[Tool: create_ticket]:::tool
  COND -->|notify| AP[/Approval: notify customer?/]:::appr
  AP --> NT[Tool: send_notification]:::tool
  TK --> DONE([Complete: resolved]):::done
  NT --> DONE

  classDef trig fill:#6ea8ff22,stroke:#6ea8ff,color:#cfe0ff;
  classDef ai fill:#c084fc22,stroke:#c084fc,color:#e9d5ff;
  classDef tool fill:#4ade8022,stroke:#4ade80,color:#bbf7d0;
  classDef cond fill:#fbbf2422,stroke:#fbbf24,color:#fde68a;
  classDef appr fill:#c084fc22,stroke:#c084fc,color:#e9d5ff;
  classDef done fill:#4ade8022,stroke:#4ade80,color:#bbf7d0;
  classDef err fill:#f8717122,stroke:#f87171,color:#fecaca;
```

The approval node maps to the runtime's real `pending_approval` gate: when the
run reaches `send_notification` (a sensitive tool), execution suspends until a
human approves in the Execution Monitor.
