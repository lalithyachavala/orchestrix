import { ReactNode } from "react";

const STATUS: Record<string, { cls: string; label: string }> = {
  queued: { cls: "bg-edge text-sub", label: "queued" },
  running: { cls: "bg-brand/15 text-brand", label: "running" },
  pending_approval: { cls: "bg-sens/15 text-sens", label: "needs approval" },
  completed: { cls: "bg-ok/15 text-ok", label: "completed" },
  success: { cls: "bg-ok/15 text-ok", label: "success" },
  failed: { cls: "bg-bad/15 text-bad", label: "failed" },
  rejected: { cls: "bg-bad/15 text-bad", label: "rejected" },
};

export function Badge({ status }: { status: string }) {
  const s = STATUS[status] || { cls: "bg-edge text-sub", label: status };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${s.cls}`}>
      {s.label}
    </span>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-edge bg-panel ${className}`}>{children}</div>
  );
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <Card className="p-5">
      <div className="text-sm text-sub">{label}</div>
      <div className="mt-1 text-3xl font-semibold tracking-tight">{value}</div>
      {hint && <div className="mt-1 text-xs text-sub">{hint}</div>}
    </Card>
  );
}

export function KV({ obj }: { obj: any }) {
  return (
    <pre className="overflow-x-auto rounded-lg bg-bg px-3 py-2 text-xs leading-relaxed text-ink/90 font-mono">
      {JSON.stringify(obj, null, 2)}
    </pre>
  );
}
