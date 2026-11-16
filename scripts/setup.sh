#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
[ -f backend/.env ] || cp backend/.env.example backend/.env
(cd frontend && npm ci)
(cd backend && ../.venv/bin/python seed.py)
echo 'Ready. Run scripts/start.sh and visit http://localhost:5173'
