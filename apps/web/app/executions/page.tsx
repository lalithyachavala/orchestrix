"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Execution } from "@/lib/api";
import { Badge, Card } from "@/components/ui";

export default function ExecutionsPage() {
  const [execs, setExecs] = useState<Execution[]>([]);
  useEffect(() => {
    const load = () => api.executions().then(setExecs).catch(() => {});
    load();
    const t = setInterval(load, 2500);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-8 py-8">
      <h1 className="text-2xl font-semibold tracking-tight">Executions</h1>
      <p className="mt-1 text-sm text-sub">Every agent run, with its full tool-call trace.</p>
      <Card className="mt-6 divide-y divide-edge">
        {execs.length === 0 && <div className="p-5 text-sm text-sub">No executions yet.</div>}
        {execs.map((e) => (
          <Link key={e.id} href={`/executions/${e.id}`}
            className="flex items-center gap-4 px-4 py-3 hover:bg-panel2">
            <span className="font-mono text-xs text-sub">{e.id}</span>
            <span className="min-w-0 flex-1 truncate text-sm">{e.task}</span>
            <span className="text-xs text-sub">{e.agent_name}</span>
            <span className="text-xs text-sub">
              {e.steps.filter((s) => s.kind === "tool").length} calls
            </span>
            <Badge status={e.status} />
          </Link>
        ))}
      </Card>
    </div>
  );
}
