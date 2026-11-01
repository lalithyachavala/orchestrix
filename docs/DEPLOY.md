# Deploying the Orchestrix public demo (Render)

Hosts **two** services — the FastAPI api and the Next.js web — as Docker
containers on [Render](https://render.com). Keyless (mock adapter), shared
synthetic data, no sign-in. All users hit the same instance, so they all see
the same agents and executions.

> You run these steps under **your own** Render + GitHub accounts. Nothing here
> uses, or should use, any other account.

## Why this shape (not serverless)

The api keeps execution state and the live SSE stream **in one long-lived
process** (single worker). Serverless/edge (Vercel functions, Lambda) would
wipe the SQLite file and split the approval/stream state across invocations.
A container host is the right fit.

## 0. One-time: bump Next (security)

The pinned `next@14.2.33` has an upstream advisory. Before a public deploy:

```bash
cd apps/web
npm install next@latest   # stay on 14.2.x, or move to 15 and retest
npm run build             # confirm it still compiles
```

## 1. Put the code on GitHub

Render deploys from a git repo.

```bash
cd <repo-root>/orchestrix       # the folder containing render.yaml
git init && git add . && git commit -m "Orchestrix demo"
# create an EMPTY repo on your GitHub, then:
git remote add origin https://github.com/<you>/orchestrix.git
git branch -M main && git push -u origin main
```

`.gitignore` already excludes `.env*`, `node_modules`, `.venv`, `*.db` — no
secrets or local API URLs ship.

## 2. Deploy the Blueprint

1. Render Dashboard → **New → Blueprint**.
2. Connect the GitHub repo. Render reads [`../render.yaml`](../render.yaml) and
   proposes two services: `orchestrix-api` and `orchestrix-web`.
3. **Apply**. Render builds both Docker images and deploys.

The blueprint already wires the cross-URLs:
- web builds with `NEXT_PUBLIC_API_BASE=https://orchestrix-api.onrender.com`
- api allows CORS from `https://orchestrix-web.onrender.com`

**If you change a service name**, update the matching URL in the other
service's env vars in `render.yaml` (or in the dashboard) and redeploy — the
URLs are derived from the names.

## 3. Use it

Open `https://orchestrix-web.onrender.com`. Share that link — anyone can run
agents, hit the approval gate, and watch executions stream. Same data for all.

Reset the demo any time:

```bash
curl -X POST https://orchestrix-api.onrender.com/admin/reset
```

## Caveats (free tier)

- **Cold start:** free services sleep after ~15 min idle; first hit takes
  ~30–60s to wake.
- **Ephemeral data:** free instances have no persistent disk, so a restart/
  redeploy **reseeds** to the default data + three agents. Good enough for a
  demo; for durable state, use a paid instance and the commented `disk` +
  `ORCHESTRIX_DB=/data/orchestrix.db` in `render.yaml`.
- **No auth:** the demo is open by design. Don't put anything real behind it.
- **Single worker only.** Don't scale the api past one instance/worker — the
  SSE queue and run loop are in-process. Horizontal scale needs Postgres + a
  shared broker (see the case study).

## Test the containers locally first (optional)

```bash
cd infra
docker compose up --build
# web → http://localhost:3000   api → http://localhost:8000
```
