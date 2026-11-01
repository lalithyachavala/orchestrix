// Thin client for the Orchestrix API. Browser-side fetch + EventSource.

export const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export type ToolSchema = {
  name: string;
  description: string;
  sensitive: boolean;
  parameters: Record<string, any>;
};

export type Agent = {
  id: string;
  name: string;
  instructions: string;
  tools: string[];
  max_steps: number;
  created_at: string;
};

export type StepStatus =
  | "running" | "success" | "failed" | "pending_approval" | "rejected";
export type ExecStatus =
  | "queued" | "running" | "pending_approval" | "completed" | "failed";

export type ExecutionStep = {
  index: number;
  kind: "reason" | "tool" | "finish";
  status: StepStatus;
  tool?: string | null;
  sensitive: boolean;
  args: Record<string, any>;
  observation: any;
  error?: string | null;
  attempts: number;
  thought?: string | null;
  ts: string;
};

export type Execution = {
  id: string;
  agent_id: string;
  agent_name: string;
  task: string;
  status: ExecStatus;
  steps: ExecutionStep[];
  summary?: string | null;
  created_at: string;
  updated_at: string;
};

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!r.ok) throw new Error((await r.text()) || r.statusText);
  return r.json();
}

export const api = {
  tools: () => j<{ tools: ToolSchema[] }>("/tools"),
  agents: () => j<Agent[]>("/agents"),
  createAgent: (body: Partial<Agent>) =>
    j<Agent>("/agents", { method: "POST", body: JSON.stringify(body) }),
  executions: () => j<Execution[]>("/executions"),
  execution: (id: string) => j<Execution>(`/executions/${id}`),
  run: (agent_id: string, task: string) =>
    j<Execution>("/executions", { method: "POST", body: JSON.stringify({ agent_id, task }) }),
  approve: (id: string) => j(`/executions/${id}/approve`, { method: "POST" }),
  reject: (id: string) => j(`/executions/${id}/reject`, { method: "POST" }),
  retry: (id: string) => j(`/executions/${id}/retry`, { method: "POST" }),
  multiAgent: (task: string) =>
    j<{ task: string; supervisor_plan: any[]; child_executions: string[]; note: string }>(
      "/multi-agent/run", { method: "POST", body: JSON.stringify({ task }) }),
};

export function streamExecution(id: string, onEvent: (e: any) => void): () => void {
  const es = new EventSource(`${API}/executions/${id}/stream`);
  es.onmessage = (m) => {
    try { onEvent(JSON.parse(m.data)); } catch {}
  };
  es.onerror = () => es.close();
  return () => es.close();
}
