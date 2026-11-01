import { Handle, Position } from "@xyflow/react";
import {
  Bot, CheckCircle2, GitBranch, Play, ShieldAlert, Wrench, XCircle,
} from "lucide-react";

export type NodeKind =
  | "trigger" | "ai" | "tool" | "conditional" | "approval" | "completion" | "error";

const STYLE: Record<NodeKind, { color: string; icon: any; label: string }> = {
  trigger: { color: "#6ea8ff", icon: Play, label: "Trigger" },
  ai: { color: "#c084fc", icon: Bot, label: "AI Reasoning" },
  tool: { color: "#4ade80", icon: Wrench, label: "Tool" },
  conditional: { color: "#fbbf24", icon: GitBranch, label: "Condition" },
  approval: { color: "#c084fc", icon: ShieldAlert, label: "Approval" },
  completion: { color: "#4ade80", icon: CheckCircle2, label: "Complete" },
  error: { color: "#f87171", icon: XCircle, label: "Error" },
};

export default function FlowNode({ data }: { data: { kind: NodeKind; label: string; sub?: string } }) {
  const s = STYLE[data.kind];
  const Icon = s.icon;
  const hasIn = data.kind !== "trigger";
  const hasOut = data.kind !== "completion" && data.kind !== "error";
  return (
    <div className="w-52 rounded-xl border bg-panel2 shadow-lg"
      style={{ borderColor: s.color + "66" }}>
      {hasIn && <Handle type="target" position={Position.Top} style={{ background: s.color }} />}
      <div className="flex items-center gap-2 rounded-t-xl px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wide"
        style={{ background: s.color + "22", color: s.color }}>
        <Icon size={13} /> {s.label}
      </div>
      <div className="px-3 py-2">
        <div className="text-sm text-ink">{data.label}</div>
        {data.sub && <div className="mt-0.5 font-mono text-[11px] text-sub">{data.sub}</div>}
      </div>
      {hasOut && <Handle type="source" position={Position.Bottom} style={{ background: s.color }} />}
    </div>
  );
}
