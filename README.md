# YEP — spaces, thoughtfully transformed

A local Software Engineering portfolio application for building finishing, renovation and project management. Built from scratch in this repository with **React 19, TypeScript, Tailwind CSS 4, Three.js, FastAPI and MongoDB**. No cloud database, paid API, external authentication, payment gateway or Docker is required.

## Get the completed source

The completed implementation is on `codex/complete-yep-requirements`; the initial preservation branch remains available. To clone the completed branch:

```powershell
git clone --branch codex/complete-yep-requirements https://github.com/yuva-bavisetti/YEP-Software-Engineering.git
cd YEP-Software-Engineering
```

## Run on Windows

Install these prerequisites first:

1. **Python 3.12** (enable the Python launcher during installation): <https://www.python.org/downloads/>
2. **Node.js 22 LTS or newer** with npm: <https://nodejs.org/>
3. **MongoDB Community Server 8.0**: <https://www.mongodb.com/try/download/community>. In the Windows installer, choose **Install MongoDB as a Service**. MongoDB Compass is optional.
4. Open Windows Services (`services.msc`) and confirm the **MongoDB** service is running. The application connects to `mongodb://127.0.0.1:27017`; no remote MongoDB account is needed.

From PowerShell in this repository:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Setup creates `.venv`, installs backend and frontend dependencies, copies the environment example if missing, creates MongoDB indexes, and seeds demo records. It does **not** overwrite existing users or reset existing records. Start opens separate backend and frontend terminal windows. Close both windows to stop the application.

- Website and dashboards: **http://localhost:5173**
- Backend interactive API docs: **http://localhost:8000/docs**
- Backend/database health: **http://localhost:8000/api/health**

Always use `localhost:5173` in the browser, matching the configured frontend origin. Avoid mixing `localhost` and `127.0.0.1` for browser sessions.

### Manual startup / troubleshooting

If PowerShell scripts are unavailable, run these commands from the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env # only if .env does not exist
cd frontend
npm ci
cd ..\backend
..\.venv\Scripts\python.exe seed.py
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, from the repository root:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

If MongoDB is unavailable, the health/API response explains that the MongoDB service and `backend/.env` need checking. In an **Administrator** PowerShell, `Start-Service MongoDB` starts an installed MongoDB service. If you chose not to install a service, start `mongod.exe` with a writable data directory, for example:

```powershell
New-Item -ItemType Directory -Force .\work\mongo-data
& 'C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe' --dbpath "$PWD\work\mongo-data" --bind_ip 127.0.0.1
```

Keep that terminal open. The MongoDB directory above may differ for your installed version. The app does not create a fake database if MongoDB is missing. A port-in-use error means an existing server must be stopped or your local configuration changed consistently.

### Environment

`backend/.env`:

```dotenv
MONGO_URL=mongodb://127.0.0.1:27017
MONGO_DB=yep
FRONTEND_ORIGIN=http://localhost:5173
UPLOAD_DIR=uploads
COOKIE_SECURE=false
```

Run backend commands from `backend/`, so the relative upload directory is `backend/uploads/`. Use an absolute `UPLOAD_DIR` if changing the backend working directory. The Vite development proxy forwards `/api` to `http://127.0.0.1:8000`; `YEP_API_PROXY` can override that target for development. Keep `COOKIE_SECURE=false` for HTTP localhost; secure cookies require HTTPS.

### Linux/macOS

With Python, Node and a local MongoDB already installed and running:

```bash
bash scripts/setup.sh
bash scripts/start.sh
```

## Demo accounts — development only

All four accounts use **`Demo@12345`**. Passwords are bcrypt-hashed; authentication uses revocable, opaque HttpOnly cookie sessions whose token hashes are stored in MongoDB.

| Workspace | Email |
|---|---|
| Customer | `customer@yep.local` |
| Owner / Admin | `owner@yep.local` |
| Manager | `manager@yep.local` |
| Worker | `worker@yep.local` |

The login page also provides demo account shortcuts. Registration creates **Customer** accounts only. Admin creates employees. These public demo credentials are for a local demonstration, not a public production deployment.

The seed creates an active customer request, completed Admin inspection, accepted Phase 1, assigned manager and worker, four milestones, a task, two phase quotations with two-page local sample PDFs, pending and verified progress photographs, both chats, a material requirement, a quality review, and one partial offline payment. The active **Morgan residence** demo project has **₹1,30,000 payable, ₹30,000 paid and ₹1,00,000 remaining**. A separate **Completed studio refresh · Demo** project demonstrates completed milestones, verified photos, feedback and public portfolio publishing. Photographs are locally generated room **illustrations**, not claims of real completed work. Re-running `seed.py` preserves existing records and credentials.

## Implemented workflow

1. A visitor uses the public homepage's single prominent **Start New Project** button. The intended request flow survives login/registration.
2. Customers submit service/property details and optional photographs. Requests go directly to Admin; managers and workers cannot read them.
3. Admin reviews requests, requests additional information, rejects requests, or schedules/completes an inspection with measurements, findings, materials and photos. Customers can supply a requested clarification and additional photographs.
4. Only Admin can create a quotation, and only after a completed inspection. Quotations require a duration and PDF. Optional BOQ line items support material/labour/other categories, quantity, unit price, tax and discount, with server-validated totals. Drafts can be edited; published quotations remain immutable and revisions are separate records.
5. Customers view PDFs and accept, reject or request revision. Phase 1 acceptance is mandatory before Admin creates a project. Duplicate approvals and duplicate project creation are blocked.
6. Admin creates the project and assigns a manager. Admin and that manager define/manage milestones, schedule phases, assign workers, create tasks and manage execution. Workers see only assigned projects and their own tasks.
7. Every project has exactly two channels: **Internal Team Chat** and **Customer Project Chat**. No independent direct messaging exists. Workers cannot access customer chat; customers cannot access internal chat.
8. Internal photos are pending verification. Admin/assigned manager can reject them or approve and share the same stored file in customer chat. Verification identity/time and the source reference are retained. Pending evidence is inaccessible to customers, including direct file URLs.
9. Subsequent phase quotations belong to the same project. Admin publishes them and sets phase schedules. Only the respective Customer and Admin can read quotation records/PDFs or finances.
10. Admin records offline-verified instalments with date, method, reference, verification details and an idempotency key. Customers see payable/paid/balance and payment history. Audited reversals retain the original record; there is no payment deletion or online gateway.
11. Admin/manager record materials, shortages, quality checks, defects and corrective actions. Completion requires all phases and milestones complete, all tasks complete, and a passed latest quality inspection. Customers can then submit feedback.

Public pages include Home, Services and service details, Projects (published completed database projects and verified photographs), About, How It Works and Contact. Contact submissions appear in Admin's enquiries. The homepage contains a local procedural animated Three.js house with neutral-to-finished colours, windows, door and landscaping, a WebGL fallback, reduced-motion support and a separately loaded 3D bundle.

All four workspaces include their permitted projects, role-specific navigation, notifications and profiles. Admin additionally manages employee activation, services, customers, enquiries, audit history and database-backed reports. Project galleries respect the same channel/file permissions as their source messages.

### AI interfaces

Customer **AI Design Studio, AI Design Assistant, AI Cost Estimator, Smart Recommendations and AI Project Insights** contain their own inputs, upload/preview controls and setup panels. They explicitly explain that no provider is connected. Selecting colours affects the selected palette only; uploaded images remain original. No AI results, cost estimates, chat answers or recommendations are fabricated. No external AI API or key is used. These are newly recreated interfaces; no old source was available to preserve.

### Financial rules

- Money is stored and summed in integer **paise**, displayed as INR.
- Total payable includes the accepted initial quotation and currently published/accepted subsequent quotations. Draft, rejected and revision-requested records are excluded. Each phase can have only one undecided/accepted current quotation; history is retained.
- Phase 1 acceptance is required to start the project. Acceptance of later phases is optional; a published later-phase quote is included in payable until rejected or sent for revision.
- Receipts are verified offline payments, net of reversals. Quotation value is **not** reported as revenue.
- An overpayment is retained as a negative balance (customer credit), rather than silently discarding a real receipt. Admin should verify amounts carefully.
- Uploaded PDF content is not parsed to extract/validate its written totals; Admin must ensure it matches the structured quotation.

## Project structure

```text
backend/
  app/main.py            FastAPI endpoints, persistence and workflow orchestration
  app/models.py          Strict Pydantic request models and validation
  app/permissions.py     Shared role, project, financial and chat policies
  app/quotations.py      Exact BOQ calculations and monetary rounding
  app/demo_assets.py     Offline-generated two-page PDF and room illustration
  seed.py                Non-destructive demonstration seed
  reset_demo.py          Explicit development database reset
  tests/                 API workflow, privacy, seed and restart tests
  .env.example
frontend/
  src/main.tsx           Session bootstrap and public/workspace navigation
  src/pages/             Public site and authentication
  src/features/          Dashboard, projects/chats, finance, BOQ, AI, Admin panels
  src/components/        Shared forms/UI and lazy 3D wrapper
  src/House.tsx          Procedural Three.js scene
  src/api.ts             Cookie-authenticated HTTP/file client and formatting
  src/style.css          Responsive design system and Tailwind entry
  src/tests/             Component interaction and role-navigation tests
scripts/                 Windows and Unix setup/start/verification scripts
```

See the current root documents: [requirements audit](REQUIREMENTS_AUDIT.md), [test results](TEST_RESULTS.md), [architecture](ARCHITECTURE.md), [API reference](API_DOCUMENTATION.md), [database design](DATABASE_DESIGN.md), [demo guide](DEMO_GUIDE.md) and [known limitations](KNOWN_LIMITATIONS.md). The original `docs/` reports remain as baseline history. Interactive OpenAPI documentation is generated by FastAPI at `/docs`; `/openapi.json` describes every endpoint and request model.

## Tests and production build

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\test.ps1
```

Or:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm test
npm run build
```

Default backend tests use an isolated **mongomock** database, never the demo database. Frontend tests use jsdom and controlled API substitutes; they check component behavior, not browser rendering. The real-MongoDB process-restart test is skipped unless enabled:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-persistence.ps1
```

This sets `MONGO_TEST_URL` (defaults to local MongoDB), runs the same API suite against actual MongoDB, and runs a separate backend-process restart test for sessions, files, chat and payment/quotation records. Every integration test uses a uniquely named `yep_test_*` database and removes only that database afterwards. The seed-repeatability test intentionally remains isolated with mongomock.

## Reset / backup

Seed again without resetting anything:

```powershell
cd backend
..\.venv\Scripts\python.exe seed.py
```

For a clean demonstration without touching existing data, use a new `MONGO_DB`, for example `yep_demo_2`, in `.env`, then seed it. To **permanently erase** the configured development database and reseed, use an explicit matching confirmation:

```powershell
cd backend
..\.venv\Scripts\python.exe reset_demo.py --confirm-database yep
```

Uploaded files are retained by reset; old unreferenced files are not automatically deleted. For backups, stop the application, copy `backend/uploads/`, and use MongoDB Database Tools `mongodump --uri="mongodb://127.0.0.1:27017" --db=yep --out=backup`. Restore with `mongorestore` into the intended local database. Never commit uploads, `.env`, database files or session tokens.

## Current verification limits

The Linux workspace passed the API/permission tests, frontend interaction tests and TypeScript production build. MongoDB was not available here and the official binary/repository downloads returned HTTP 403, so actual disk persistence and restart verification were **not executed**. The browser preview relay also failed to start, so WebGL rendering, responsive layout and real browser flows remain **unverified**. Windows scripts are provided but were **not executed on Windows**. Run the real-MongoDB verification and presentation walkthrough on your laptop before your university demonstration.

This is a local portfolio implementation, not a hardened public production service: there is no email verification, password recovery, background job queue, malware scanner or external monitoring. See the architecture notes for atomic-write guarantees and remaining multi-document failure boundaries. The public gallery reads completed projects explicitly published by Admin. The seed adds a separate completed project with clearly labelled demonstration illustrations and feedback; these are not claims of real client work. AI processing is intentionally unintegrated.

## Completion update

The existing application has been extended in place. Added: completed-project portfolio publishing/category filters/feedback, managed service images and stored descriptions, scoped dashboard activity/current-phase/worker-instruction views, manager execution reports, material edits, structured quality checklists, planned phases and validated transitions, milestone definition edits and verified chat updates, read notifications, customer history, employee role editing and public contact settings. No external AI integration was added.

Business writes now use a renewable MongoDB lease, compare-and-set updates and idempotent recovery of derived records. Competing writes return a retryable 409; after a crashed process the lease expires in 30 seconds. Source receipts and decisions remain authoritative. This does not turn standalone MongoDB into cross-collection ACID transactions. See architecture/limitations for the precise guarantees.

A later phase must have its quotation published and preceding phases completed before activation. Add at least one milestone to each phase; verify all its milestones and finish its tasks before completion. New phase numbers are not capped at 100. Legacy tasks without a stored phase are treated as Phase 1.

The automated acceptance matrix contains all 42 specified scenarios. Test results distinguish actual API/component checks from the unavailable real-MongoDB, Windows and browser/WebGL checks; see TEST_RESULTS.md.
