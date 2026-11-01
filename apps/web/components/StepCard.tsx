import { ExecutionStep } from "@/lib/api";
import { Badge, KV } from "./ui";
import {
  Brain, CheckCircle2, CircleDot, Flag, ShieldAlert, Wrench, XCircle,
} from "lucide-react";

const ICON: Record<string, any> = {
  running: CircleDot, success: CheckCircle2, failed: XCircle,
  rejected: XCircle, pending_approval: ShieldAlert,
};
const ICON_COLOR: Record<string, string> = {
  running: "text-brand", success: "text-ok", failed: "text-bad",
  rejected: "text-bad", pending_approval: "text-sens",
};

export default function StepCard({ step }: { step: ExecutionStep }) {
  if (step.kind === "finish") {
    return (
      <Row icon={Flag} color="text-ok" line>
        <div className="text-sm font-medium text-ok">Finished</div>
        {step.thought && <div className="mt-0.5 text-xs text-sub">{step.thought}</div>}
      </Row>
    );
  }

  const Icon = ICON[step.status] || CircleDot;
  const color = ICON_COLOR[step.status] || "text-sub";

  return (
    <Row icon={Icon} color={color} line>
      <div className="flex flex-wrap items-center gap-2">
        <Wrench size={14} className="text-sub" />
        <span className="font-mono text-sm">{step.tool}</span>
        {step.sensitive && (
          <span className="inline-flex items-center gap-1 rounded bg-sens/15 px-1.5 py-0.5 text-[10px] text-sens">
            <ShieldAlert size={10} /> sensitive
          </span>
        )}
        <Badge status={step.status} />
        {step.attempts > 1 && <span className="text-[11px] text-warn">attempt {step.attempts}</span>}
      </div>

      {step.thought && (
        <div className="mt-2 flex items-start gap-2 text-xs text-sub">
          <Brain size={13} className="mt-0.5 shrink-0" />
          <span className="italic">{step.thought}</span>
        </div>
      )}

      <div className="mt-2 grid gap-2 md:grid-cols-2">
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wide text-sub">input</div>
          <KV obj={step.args} />
        </div>
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wide text-sub">output</div>
          {step.error
            ? <div className="rounded-lg bg-bad/10 px-3 py-2 text-xs text-bad">{step.error}</div>
            : step.observation != null
              ? <KV obj={step.observation} />
              : <div className="rounded-lg bg-bg px-3 py-2 text-xs text-sub">
                  {step.status === "pending_approval" ? "awaiting approval…" : "—"}
                </div>}
        </div>
      </div>
    </Row>
  );
}

function Row({ icon: Icon, color, children, line }: {
  icon: any; color: string; children: React.ReactNode; line?: boolean;
}) {
  return (
    <div className="relative flex gap-3 pb-5">
      {line && <div className="absolute left-[11px] top-7 h-full w-px bg-edge" />}
      <Icon size={22} className={`${color} shrink-0`} />
      <div className="min-w-0 flex-1 rounded-xl border border-edge bg-panel p-3">{children}</div>
    </div>
  );
}
