#!/usr/bin/env bash
# Boot Orchestrix locally (POSIX). API :8000, Web :3000. Keyless.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"

cd "$root/apps/api"
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/python -m pip install -q -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --port 8000 &

cd "$root/apps/web"
[ -d node_modules ] || npm install
echo "API on http://localhost:8000  ·  Web on http://localhost:3000"
npm run dev
