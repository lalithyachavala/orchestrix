"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, Agent, ToolSchema } from "@/lib/api";
import { Badge, Card } from "@/components/ui";
import { Bot, Play, Plus, ShieldAlert } from "lucide-react";

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tools, setTools] = useState<ToolSchema[]>([]);
  const [sel, setSel] = useState<Agent | null>(null);

  const load = () => api.agents().then(setAgents);
  useEffect(() => { load(); api.tools().then((t) => setTools(t.tools)); }, []);
  useEffect(() => { if (!sel && agents.length) setSel(agents[0]); }, [agents, sel]);

  return (
    <div className="mx-auto max-w-6xl px-8 py-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Agents</h1>
          <p className="mt-1 text-sm text-sub">Configure an agent's instructions and the tools it may call.</p>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <CreateAgent tools={tools} onCreated={(a) => { load(); setSel(a); }} />
          <h2 className="mb-2 mt-6 text-sm font-medium text-sub">All agents</h2>
          <Card className="divide-y divide-edge">
            {agents.map((a) => (
              <button key={a.id} onClick={() => setSel(a)}
                className={`flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-panel2 ${
                  sel?.id === a.id ? "bg-panel2" : ""}`}>
                <Bot size={16} className="text-brand" />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm">{a.name}</div>
                  <div className="truncate text-xs text-sub">{a.tools.length} tools</div>
                </div>
              </button>
            ))}
          </Card>
        </div>

        <div className="lg:col-span-3">
          {sel && <AgentDetail agent={sel} tools={tools}
            onRun={(id) => router.push(`/executions/${id}`)} />}
        </div>
      </div>
    </div>
  );
}

function CreateAgent({ tools, onCreated }: { tools: ToolSchema[]; onCreated: (a: Agent) => void }) {
  const [name, setName] = useState("");
  const [instructions, setInstr] = useState("");
  const [picked, setPicked] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const toggle = (n: string) =>
    setPicked((p) => (p.includes(n) ? p.filter((x) => x !== n) : [...p, n]));

  const submit = async () => {
    if (!name || !instructions || picked.length === 0) return;
    setBusy(true);
    try {
      const a = await api.createAgent({ name, instructions, tools: picked, max_steps: 8 });
      setName(""); setInstr(""); setPicked([]); onCreated(a);
    } finally { setBusy(false); }
  };

  return (
    <Card className="p-5">
      <div className="mb-3 flex items-center gap-2 text-sm font-medium"><Plus size={16} /> New agent</div>
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Agent name"
        className="mb-2 w-full rounded-lg border border-edge bg-bg px-3 py-2 text-sm outline-none focus:border-brand" />
      <textarea value={instructions} onChange={(e) => setInstr(e.target.value)} rows={3}
        placeholder="Instructions — what should this agent do?"
        className="mb-3 w-full resize-none rounded-lg border border-edge bg-bg px-3 py-2 text-sm outline-none focus:border-brand" />
      <div className="mb-3 text-xs text-sub">Available tools</div>
      <div className="mb-4 flex flex-wrap gap-2">
        {tools.map((t) => (
          <button key={t.name} onClick={() => toggle(t.name)}
            className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs transition ${
              picked.includes(t.name)
                ? "border-brand bg-brand/15 text-brand"
                : "border-edge text-sub hover:border-sub"}`}>
            {t.name}{t.sensitive && <ShieldAlert size={11} className="text-sens" />}
          </button>
        ))}
      </div>
      <button onClick={submit} disabled={busy || !name || !instructions || !picked.length}
        className="w-full rounded-lg bg-brand px-3 py-2 text-sm font-medium text-bg disabled:opacity-40">
        {busy ? "Creating…" : "Create agent"}
      </button>
    </Card>
  );
}

function AgentDetail({ agent, tools, onRun }: {
  agent: Agent; tools: ToolSchema[]; onRun: (id: string) => void;
}) {
  const [task, setTask] = useState("");
  const [busy, setBusy] = useState(false);
  const sensitive = agent.tools.filter((t) => tools.find((x) => x.name === t)?.sensitive);

  const run = async () => {
    if (!task) return;
    setBusy(true);
    try { const ex = await api.run(agent.id, task); onRun(ex.id); }
    finally { setBusy(false); }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">{agent.name}</h2>
          <div className="font-mono text-xs text-sub">{agent.id}</div>
        </div>
        <Badge status="success" />
      </div>
      <p className="mt-4 text-sm leading-relaxed text-ink/90">{agent.instructions}</p>

      <div className="mt-4 flex flex-wrap gap-2">
        {agent.tools.map((t) => {
          const s = tools.find((x) => x.name === t)?.sensitive;
          return (
            <span key={t} className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs ${
              s ? "border-sens/40 text-sens" : "border-edge text-sub"}`}>
              {t}{s && <ShieldAlert size={11} />}
            </span>
          );
        })}
      </div>
      {sensitive.length > 0 && (
        <div className="mt-3 text-xs text-sens">
          {sensitive.length} sensitive tool(s) — calls pause for human approval before executing.
        </div>
      )}

      <div className="mt-6 border-t border-edge pt-5">
        <div className="mb-2 text-sm font-medium">Run a task</div>
        <textarea value={task} onChange={(e) => setTask(e.target.value)} rows={2}
          placeholder="e.g. Cedar Health order ORD-5003 is delayed past SLA — open an urgent ticket and notify them"
          className="mb-3 w-full resize-none rounded-lg border border-edge bg-bg px-3 py-2 text-sm outline-none focus:border-brand" />
        <button onClick={run} disabled={busy || !task}
          className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-bg disabled:opacity-40">
          <Play size={15} /> {busy ? "Starting…" : "Run agent"}
        </button>
      </div>
    </Card>
  );
}
