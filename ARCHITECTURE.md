# YEP architecture

YEP retains React 19 + TypeScript + Tailwind 4 + Three.js, FastAPI/Python, local MongoDB and private local file storage. It is a modular monolith, not a hosted service or a replacement application.

## Source modules

- `frontend/src/pages/`: public site and authentication. Existing layout, navigation and main forms are retained.
- `frontend/src/features/`: role dashboard, project/phases/tasks/chats, materials/quality/gallery, BOQ, finances, AI interfaces, public portfolio, service catalogue, reports, customer history and settings.
- `frontend/src/components/`: shared accessible form controls and lazy Three.js wrapper. File inputs are explicitly copied into submitted FormData, including multiple files.
- `frontend/src/House.tsx`, `houseAnimation.ts`: procedural geometry and a deterministic unfinished → finished timeline; doors/windows/finishes and landscaping join the transformation. Reduced motion displays a static finished scene.
- `backend/app/main.py`: existing API/business orchestration retained and extended in place.
- `backend/app/models.py`, `permissions.py`, `quotations.py`: strict Pydantic validation, shared role/project/chat policies and exact monetary arithmetic.
- `backend/app/enhancements.py`: additional scoped dashboard/reports, public portfolio/assets, materials editing, customer history and settings APIs. Uses the same injected database as the existing routes/tests.
- `backend/app/assets.py`: Pillow and pypdf validation before storing images/documents.
- `backend/app/serialization.py`: renewable MongoDB business-write lease, shared across backend processes using the same database.
- `backend/app/recovery.py`: idempotent reconstruction of derived request histories/statuses, quotation/project links, published phases, aggregate progress and verified milestone messages from durable source records.
- `backend/seed.py`, `seed_portfolio.py`: non-destructive active and completed demonstration workflows through real application APIs.

## Authorization

Admin alone reviews initial requests, records inspections, prepares/publishes quotations, creates projects after accepted Phase 1, assigns managers, manages finances and controls public publishing. Assigned managers execute their projects and assign workers. Workers have assigned projects and only their own tasks. Customers have their own requests, projects, quotations, finances and Customer Chat. Every project has exactly two channel names, enforced on every chat and private file request.

Manager/worker DTOs remove quotation references; workers also do not receive customer identity fields. Finance endpoints/PDFs independently enforce Admin/customer ownership. The public portfolio exposes only chosen verified photographs, public text/category and optionally selected feedback—not addresses, contacts, chats, staff identities or money. Service photographs become public only through an active service's dedicated asset endpoint.

## State and consistency

- Inspections are conditional writes; completion is immutable. Scheduled inspection edits retain prior photographs.
- Draft publication and customer decisions use compare-and-set conditions. Phase/revision uniqueness prevents competing duplicate quotation records. Draft edits cannot overwrite a published quotation.
- Projects have a unique originating request; workers use `$addToSet`. Canonical membership is evaluated at request time, so reassigned/unassigned users cannot retain historical access through old links.
- Phase numbers have no 100-phase application cap. Planned phases may exist before a quote; activation requires its published/accepted quotation, dates, and completed preceding phases. Planned → Active → Completed transitions are enforced; completed phases are immutable.
- Milestone progress comes only from Admin/assigned manager. Completion checks exact per-milestone values, not a rounded average. Explicit verified milestone publishing creates a recoverable customer-chat event. Worker evidence never automatically completes a milestone.
- Task execution requires an active project and active associated phase. Staff can reassign/update tasks only to project members. Completed/on-hold execution is blocked server-side.
- Evidence verification is a conditional Pending → Approved/Rejected write. Approval and later sharing, or one combined approval/share, reuse the same file. Deterministic customer message IDs prevent duplicate publication and allow reconstruction after interruption.
- Quotation amounts and receipt entries are integer paise. BOQ/tax/discount use Decimal/half-up rounding on the server and BigInt arithmetic in the UI. Draft/rejected/revision-requested records are excluded from payable. Receipts and uniquely keyed reversals are append-only; overpayments remain visible as credit.
- Completion requires all phases complete, milestones verified at 100%, tasks complete and latest quality inspection passed. Each completed phase needs defined/verified milestones. Structured checklist failures cannot be saved as passed inspections.

### Standalone MongoDB write coordination

Authenticated business writes acquire one renewable MongoDB lease before handler execution. Its atomic unique `_id` acquisition prevents competing cross-collection business mutations; another writer receives a retryable 409. The lease renews every five seconds and expires 30 seconds after a crashed process stops renewing. It is released in `finally`. This intentionally favors correctness and simplicity for a local demonstration over parallel write throughput.

Canonical documents use atomic writes/unique constraints. Recoverable derived views are replayed at startup and relevant reads/writes, so interruption does not require deleting records or resetting the database. Audit/notification writes are separate records; source receipts and verification metadata remain authoritative. This is **not** a cross-collection ACID transaction or a claim of arbitrary crash-proof behavior. Read projections are eventually reconciled; a loss of database connectivity can still interrupt a response after its source write commits. Real-engine multi-process/crash stress verification is not claimed. See KNOWN_LIMITATIONS.md.

## AI boundary

All five customer interfaces remain independent input/setup modules: Design Studio, Design Assistant, Cost Estimator, Recommendations and Project Insights. No external AI adapter is configured, no paid API is required and no generated result is simulated. Upload previews stay original; choosing a palette is not presented as image processing.

## Operation

The Vite development proxy sends `/api` to the local FastAPI process. MongoDB and uploads persist outside the frontend build. Credentials/env files, dependencies, generated data and scratch work are ignored by Git. PowerShell setup/start/test/persistence scripts remain the supported Windows path. See README.md, DATABASE_DESIGN.md, API_DOCUMENTATION.md, DEMO_GUIDE.md and TEST_RESULTS.md.
