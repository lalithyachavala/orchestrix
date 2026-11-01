"use client";
import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { api, Execution, ExecutionStep, streamExecution } from "@/lib/api";
import { Badge, Card } from "@/components/ui";
import StepCard from "@/components/StepCard";
import { Check, RotateCw, ShieldAlert, X } from "lucide-react";

export default function MonitorPage() {
  const { id } = useParams<{ id: string }>();
  const [ex, setEx] = useState<Execution | null>(null);
  const [steps, setSteps] = useState<ExecutionStep[]>([]);
  const [status, setStatus] = useState<string>("queued");
  const [summary, setSummary] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.execution(id).then((e) => {
      setEx(e); setSteps(e.steps); setStatus(e.status); setSummary(e.summary ?? null);
    });
    const stop = streamExecution(id, (evt) => {
      if (evt.steps) setSteps(evt.steps);
      if (evt.status) setStatus(evt.status);
      if (evt.summary !== undefined) setSummary(evt.summary);
    });
    return stop;
  }, [id]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [steps.length]);

  const act = async (fn: () => Promise<any>) => {
    setBusy(true);
    try {
      await fn();
      // reopen stream to pick up the resumed run
      const e = await api.execution(id); setStatus(e.status);
      streamExecution(id, (evt) => {
        if (evt.steps) setSteps(evt.steps);
        if (evt.status) setStatus(evt.status);
        if (evt.summary !== undefined) setSummary(evt.summary);
      });
    } finally { setBusy(false); }
  };

  if (!ex) return <div className="p-8 text-sm text-sub">Loading…</div>;
  const toolCalls = steps.filter((s) => s.kind === "tool").length;

  return (
    <div className="mx-auto max-w-4xl px-8 py-8">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="font-mono text-xs text-sub">{ex.id} · {ex.agent_name}</div>
          <h1 className="mt-1 text-xl font-semibold leading-snug">{ex.task}</h1>
        </div>
        <Badge status={status} />
      </div>

      <div className="mt-3 flex items-center gap-4 text-xs text-sub">
        <span>{toolCalls} tool call{toolCalls === 1 ? "" : "s"}</span>
        {status === "running" && <span className="text-brand">● live</span>}
      </div>

      {status === "pending_approval" && (
        <Card className="mt-5 border-sens/40 bg-sens/5 p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-sens">
            <ShieldAlert size={16} /> Human approval required
          </div>
          <p className="mt-1 text-xs text-sub">
            The agent wants to run a sensitive tool. Nothing executes until you decide.
          </p>
          <div className="mt-3 flex gap-2">
            <button onClick={() => act(() => api.approve(id))} disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-lg bg-ok px-3 py-1.5 text-sm font-medium text-bg disabled:opacity-40">
              <Check size={15} /> Approve
            </button>
            <button onClick={() => act(() => api.reject(id))} disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-lg border border-bad px-3 py-1.5 text-sm font-medium text-bad disabled:opacity-40">
              <X size={15} /> Reject
            </button>
          </div>
        </Card>
      )}

      {status === "failed" && (
        <Card className="mt-5 border-bad/40 bg-bad/5 p-4">
          <div className="text-sm font-medium text-bad">A tool call failed after retries.</div>
          <p className="mt-1 text-xs text-sub">Re-drive the failed step once the cause is addressed.</p>
          <button onClick={() => act(() => api.retry(id))} disabled={busy}
            className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-edge px-3 py-1.5 text-sm hover:border-sub disabled:opacity-40">
            <RotateCw size={14} /> Retry
          </button>
        </Card>
      )}

      {summary && status === "completed" && (
        <Card className="mt-5 border-ok/30 bg-ok/5 p-4 text-sm text-ink/90">
          <span className="text-ok">Summary · </span>{summary}
        </Card>
      )}

      <h2 className="mb-3 mt-7 text-sm font-medium text-sub">Execution timeline</h2>
      <div>
        {steps.map((s) => <StepCard key={s.index} step={s} />)}
        {steps.length === 0 && <div className="text-sm text-sub">Waiting for the first step…</div>}
        <div ref={endRef} />
      </div>
    </div>
  );
}
