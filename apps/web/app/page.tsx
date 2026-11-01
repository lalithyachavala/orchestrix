"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Agent, Execution, ToolSchema } from "@/lib/api";
import { Badge, Card, Stat, KV } from "@/components/ui";
import { ShieldAlert, Wrench } from "lucide-react";

export default function Overview() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [execs, setExecs] = useState<Execution[]>([]);
  const [tools, setTools] = useState<ToolSchema[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    Promise.all([api.agents(), api.executions(), api.tools()])
      .then(([a, e, t]) => { setAgents(a); setExecs(e); setTools(t.tools); })
      .catch((e) => setErr(String(e)));
  }, []);

  const completed = execs.filter((e) => e.status === "completed").length;
  const toolCalls = execs.reduce(
    (n, e) => n + e.steps.filter((s) => s.kind === "tool" && s.status === "success").length, 0);

  return (
    <div className="mx-auto max-w-6xl px-8 py-8">
      <h1 className="text-2xl font-semibold tracking-tight">Overview</h1>
      <p className="mt-1 text-sm text-sub">
        A single plane for building, running, and auditing tool-using AI agents.
      </p>

      {err && <Card className="mt-4 border-bad/40 p-4 text-sm text-bad">
        API unreachable at the configured base URL. Is the FastAPI server running on :8000? <br />{err}
      </Card>}

      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Agents" value={agents.length} />
        <Stat label="Executions" value={execs.length} hint={`${completed} completed`} />
        <Stat label="Successful tool calls" value={toolCalls} />
        <Stat label="Tools available" value={tools.length} />
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <h2 className="mb-3 text-sm font-medium text-sub">Recent executions</h2>
          <Card className="divide-y divide-edge">
            {execs.length === 0 && <div className="p-5 text-sm text-sub">No executions yet. Start one from Agents.</div>}
            {execs.slice(0, 7).map((e) => (
              <Link key={e.id} href={`/executions/${e.id}`}
                className="flex items-center gap-3 px-4 py-3 hover:bg-panel2">
                <span className="font-mono text-xs text-sub">{e.id}</span>
                <span className="min-w-0 flex-1 truncate text-sm">{e.task}</span>
                <span className="text-xs text-sub">{e.agent_name}</span>
                <Badge status={e.status} />
              </Link>
            ))}
          </Card>
        </div>

        <div className="lg:col-span-2">
          <h2 className="mb-3 text-sm font-medium text-sub">Tool catalog</h2>
          <Card className="divide-y divide-edge">
            {tools.map((t) => (
              <div key={t.name} className="flex items-start gap-3 px-4 py-3">
                <Wrench size={15} className="mt-0.5 text-sub" />
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm">{t.name}</span>
                    {t.sensitive && (
                      <span className="inline-flex items-center gap-1 rounded bg-sens/15 px-1.5 py-0.5 text-[10px] text-sens">
                        <ShieldAlert size={11} /> approval
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-sub">{t.description}</div>
                </div>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}
