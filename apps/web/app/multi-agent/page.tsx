"use client";
import { useState } from "react";
import Link from "next/link";
import { api, Execution } from "@/lib/api";
import { Badge, Card } from "@/components/ui";
import { ArrowRight, FlaskConical, Network, Play } from "lucide-react";

const ROLE_COLOR: Record<string, string> = {
  research: "#6ea8ff", analysis: "#fbbf24", execution: "#4ade80",
};

export default function MultiAgentPage() {
  const [task, setTask] = useState(
    "Cedar Health is at risk after a delayed order — investigate, report, open a ticket and update their CRM");
  const [busy, setBusy] = useState(false);
  const [plan, setPlan] = useState<any[]>([]);
  const [children, setChildren] = useState<Execution[]>([]);
  const [err, setErr] = useState("");

  const run = async () => {
    setBusy(true); setErr(""); setChildren([]); setPlan([]);
    try {
      const r = await api.multiAgent(task);
      setPlan(r.supervisor_plan);
      const execs = await Promise.all(r.child_executions.map((id) => api.execution(id)));
      setChildren(execs);
    } catch (e) { setErr(String(e)); } finally { setBusy(false); }
  };

  return (
    <div className="mx-auto max-w-5xl px-8 py-8">
      <div className="flex items-center gap-2">
        <h1 className="text-2xl font-semibold tracking-tight">Multi-Agent</h1>
        <span className="inline-flex items-center gap-1 rounded-full bg-warn/15 px-2.5 py-0.5 text-xs font-medium text-warn">
          <FlaskConical size={12} /> experimental
        </span>
      </div>
      <p className="mt-1 text-sm text-sub">
        A supervisor decomposes one task and routes it to specialized agents:
        <span className="text-brand"> research</span> →
        <span className="text-warn"> analysis</span> →
        <span className="text-ok"> execution</span>. Approval is auto-granted across the
        chain for the demo; single-agent runs keep real human approval.
      </p>

      <Card className="mt-6 p-5">
        <textarea value={task} onChange={(e) => setTask(e.target.value)} rows={2}
          className="mb-3 w-full resize-none rounded-lg border border-edge bg-bg px-3 py-2 text-sm outline-none focus:border-brand" />
        <button onClick={run} disabled={busy || !task}
          className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-bg disabled:opacity-40">
          <Play size={15} /> {busy ? "Supervisor coordinating…" : "Run supervisor"}
        </button>
      </Card>

      {err && <Card className="mt-4 border-bad/40 p-4 text-sm text-bad">{err}</Card>}

      {plan.length > 0 && (
        <div className="mt-6">
          <div className="mb-3 flex items-center gap-2 text-sm font-medium text-sub">
            <Network size={15} /> Supervisor plan
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {plan.map((p, i) => (
              <span key={p.role} className="flex items-center gap-2">
                <span className="rounded-lg border px-3 py-1.5 text-xs capitalize"
                  style={{ borderColor: ROLE_COLOR[p.role] + "66", color: ROLE_COLOR[p.role] }}>
                  {p.role}
                </span>
                {i < plan.length - 1 && <ArrowRight size={14} className="text-sub" />}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {children.map((ex) => {
          const role = ex.agent_name.split(" ")[0].toLowerCase();
          const color = ROLE_COLOR[role] || "#93a0b4";
          const calls = ex.steps.filter((s) => s.kind === "tool");
          return (
            <Card key={ex.id} className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium" style={{ color }}>{ex.agent_name}</span>
                <Badge status={ex.status} />
              </div>
              <div className="mt-3 space-y-1">
                {calls.map((s) => (
                  <div key={s.index} className="flex items-center gap-2 text-xs">
                    <span className="h-1.5 w-1.5 rounded-full"
                      style={{ background: s.status === "success" ? "#4ade80" : "#f87171" }} />
                    <span className="font-mono text-sub">{s.tool}</span>
                  </div>
                ))}
              </div>
              {ex.summary && <div className="mt-3 text-xs text-sub">{ex.summary}</div>}
              <Link href={`/executions/${ex.id}`}
                className="mt-3 inline-flex items-center gap-1 text-xs text-brand hover:underline">
                full trace <ArrowRight size={12} />
              </Link>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
