"use client";
import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  addEdge, Background, Controls, MiniMap, ReactFlow, useEdgesState, useNodesState,
  type Connection, type Edge, type Node, MarkerType,
} from "@xyflow/react";
import FlowNode, { NodeKind } from "@/components/FlowNode";
import { api } from "@/lib/api";
import { Play } from "lucide-react";

// A default graph modelling the Support Resolver pipeline. The builder is a
// real editor (add nodes, drag, connect); "Run" executes the agent for real.
const INIT_NODES: Node[] = [
  n("t", "trigger", "Inbound request", 300, 0),
  n("ai", "ai", "Classify & plan", "mock planner", 300, 110),
  n("c1", "tool", "Look up customer", "search_customers", 300, 220),
  n("c2", "tool", "Retrieve order", "get_order", 300, 330),
  n("cond", "conditional", "Order delayed / SLA?", undefined, 300, 440),
  n("tk", "tool", "Open ticket", "create_ticket", 120, 560),
  n("ap", "approval", "Notify customer?", "human-in-the-loop", 480, 560),
  n("nt", "tool", "Send notification", "send_notification", 480, 680),
  n("done", "completion", "Resolved", undefined, 300, 800),
  n("err", "error", "Failed / retry", undefined, 40, 800),
];
const INIT_EDGES: Edge[] = [
  e("t", "ai"), e("ai", "c1"), e("c1", "c2"), e("c2", "cond"),
  e("cond", "tk", "yes"), e("cond", "ap", "notify"),
  e("tk", "done"), e("ap", "nt"), e("nt", "done"), e("c2", "err", "not found"),
];

function n(id: string, kind: NodeKind, label: string, sub?: string | number, x?: number, y?: number): Node {
  const [sx, sy] = typeof sub === "number" ? [sub, x as number] : [x as number, y as number];
  return { id, type: "orx", position: { x: sx, y: sy },
    data: { kind, label, sub: typeof sub === "string" ? sub : undefined } };
}
function e(source: string, target: string, label?: string): Edge {
  return { id: `${source}-${target}`, source, target, label, animated: true,
    style: { stroke: "#3a465c" }, labelStyle: { fill: "#93a0b4", fontSize: 11 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#3a465c" } };
}

const PALETTE: NodeKind[] = ["trigger", "ai", "tool", "conditional", "approval", "completion", "error"];

export default function WorkflowsPage() {
  const router = useRouter();
  const [nodes, setNodes, onNodesChange] = useNodesState(INIT_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INIT_EDGES);
  const [task, setTask] = useState(
    "Cedar Health order ORD-5003 is delayed past SLA — open an urgent ticket and notify them");
  const [busy, setBusy] = useState(false);
  const nodeTypes = useMemo(() => ({ orx: FlowNode }), []);

  const onConnect = useCallback(
    (c: Connection) => setEdges((eds) => addEdge({ ...c, animated: true,
      style: { stroke: "#3a465c" }, markerEnd: { type: MarkerType.ArrowClosed, color: "#3a465c" } }, eds)),
    [setEdges]);

  const addNode = (kind: NodeKind) => setNodes((ns) => [...ns,
    n(`${kind}-${ns.length}`, kind, kind[0].toUpperCase() + kind.slice(1), undefined,
      360 + (ns.length % 3) * 40, 60 + ns.length * 24)]);

  const run = async () => {
    setBusy(true);
    try {
      const agents = await api.agents();
      const support = agents.find((a) => a.name === "Support Resolver") || agents[0];
      const ex = await api.run(support.id, task);
      router.push(`/executions/${ex.id}`);
    } finally { setBusy(false); }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-edge px-8 py-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Workflow Builder</h1>
          <p className="mt-1 text-sm text-sub">
            Compose triggers, reasoning, tool calls, conditions, and approval gates.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input value={task} onChange={(ev) => setTask(ev.target.value)}
            className="w-96 rounded-lg border border-edge bg-bg px-3 py-2 text-sm outline-none focus:border-brand" />
          <button onClick={run} disabled={busy}
            className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-bg disabled:opacity-40">
            <Play size={15} /> {busy ? "Starting…" : "Run workflow"}
          </button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1">
        <div className="w-44 shrink-0 border-r border-edge bg-panel p-3">
          <div className="mb-2 text-xs font-medium text-sub">Add node</div>
          <div className="flex flex-col gap-1.5">
            {PALETTE.map((k) => (
              <button key={k} onClick={() => addNode(k)}
                className="rounded-lg border border-edge px-3 py-1.5 text-left text-xs capitalize text-sub hover:border-sub hover:text-ink">
                {k}
              </button>
            ))}
          </div>
          <div className="mt-6 text-[11px] leading-relaxed text-sub">
            Drag to arrange. Drag from a handle to connect. Yellow conditions branch; the
            purple gate halts for approval.
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <ReactFlow
            nodes={nodes} edges={edges} nodeTypes={nodeTypes}
            onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect}
            fitView proOptions={{ hideAttribution: true }}
            defaultEdgeOptions={{ animated: true }}>
            <Background color="#1b212d" gap={20} />
            <Controls className="!bg-panel !border-edge" />
            <MiniMap pannable zoomable maskColor="#0b0d12cc"
              nodeColor="#273041" style={{ background: "#141821" }} />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}
