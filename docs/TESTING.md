> Baseline document retained from the initial implementation. For current behavior and verification, read [TEST_RESULTS.md](../TEST_RESULTS.md).

# Verification report

Verified in the Linux build workspace on 16 November 2026 using Python 3.12.14 and Node 24.22.1.

| Check | Result | What it establishes |
|---|---|---|
| `python -m pytest backend/tests -q` | **9 passed, 1 skipped** | Real FastAPI handlers, validation and workflow operations against isolated mongomock databases |
| `npm test` in `frontend` | **17 passed** | Role navigation, six public pages, form payloads, AI interface availability, finance rendering, draft editing and exact currency arithmetic in jsdom |
| `npm run build` in `frontend` | **Passed** | Strict TypeScript compilation and Vite production bundling |
| `python -m compileall -q backend` | **Passed** | Python source compilation |
| `bash -n scripts/setup.sh scripts/start.sh` | **Passed** | Unix shell script syntax |
| OpenAPI generation | **Passed: 48 paths / 60 operations** | Request schemas and endpoint specification exported to `backend/openapi.json` |
| Real MongoDB / backend process restart | **Skipped** | Requires `MONGO_TEST_URL` and a running MongoDB instance |
| Browser/WebGL/mobile layout QA | **Not verified** | Managed preview relay timed out before a browser preview became available |
| Windows PowerShell execution | **Not verified** | This workspace is Linux; scripts and full setup instructions are provided for laptop verification |

A dependency emits one AnyIO/Starlette TestClient deprecation warning. There are no failing tests or TypeScript/build errors in the final run. The Three.js scene is a separate lazy chunk, so it does not block the main dashboard bundle.

## Backend coverage

`test_complete_end_to_end` exercises customer login/request, direct Admin receipt, denied manager access to requests/inspections, inspection-before-quotation enforcement, PDF upload, draft privacy/publication, mandatory initial acceptance, duplicate decisions/conversion, manager/worker assignment, worker-visible phase duration, task completion, pending internal photographs, direct-file privacy, authorized verification/sharing, customer query images, Admin/manager replies, later phases on the same project, exact financial totals, duplicate payment protection, restricted financial PDFs/chats/projects, audited reversal, phase/milestone/task/quality completion gates and customer feedback.

Additional tests cover:

- Anonymous access, invalid login, foreign-origin requests, strict registration role protection, malformed payloads, invalid files and logout.
- Quotation revisions retained as separate records; draft and foreign-customer PDFs protected.
- Account deactivation blocking existing sessions and new login.
- BOQ quantity/unit extensions, tax/discount totals, mismatched-total rejection and draft-only edits.
- Customer clarification after Admin's information request, private added attachments and duplicate reply prevention.
- Negative payments, unauthorized receipt creation, zero-duration quotations and another user's uploads.
- Non-destructive, repeatable demo seeding with preservation of a user-edited project.
- Task reassignment, former-assignee access denial, new-assignee task updates, and protected milestone deadline editing.

These tests call actual application endpoints and MongoDB-style operations; they do not bypass authorization dependencies. **Mongomock is not evidence of disk durability or complete MongoDB concurrency semantics.** The normal app uses PyMongo/MongoDB and has no in-memory runtime fallback.

## Frontend coverage and limits

The component suite renders each role's workspace with controlled API responses. It checks that execution roles do not even request quotation/request endpoints, verifies request and Admin inspection form payloads, keeps all five AI screens available without external calls or fabricated responses, renders six public routes and one homepage project CTA, displays server-provided finance totals, and edits a draft while retaining its protected PDF. Currency tests cover half-paise rounding, fractional quantities, tax and discount.

These are DOM/component tests, not screenshot or real-browser end-to-end tests. The house is substituted in component tests, so WebGL, GPU support, animation, file-picker behavior, popup dialogs, keyboard/touch interaction and responsive visual appearance remain to be checked in a browser. No screenshot evidence is claimed.

## Run real database verification on Windows

Install/start MongoDB as described in README, then run from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-persistence.ps1
```

Alternatively set a local test URI explicitly and run the suite:

```powershell
$env:MONGO_TEST_URL = 'mongodb://127.0.0.1:27017'
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

With this variable set, the workflow/permission tests use real MongoDB and the skipped restart test starts a FastAPI subprocess, writes session/file/chat/quotation/payment records, restarts that backend process, and confirms the records remain. Unique `yep_test_*` databases are used and removed afterwards. The test does not stop/restart your MongoDB service; it verifies backend-process restart against the actual persistent engine.

MongoDB binaries were not installed in this workspace. Downloads from MongoDB distribution hosts returned HTTP 403, so a real database run was not possible. The browser preview CLI separately failed with a relay-readiness timeout. These were environment limitations, not passing verification results.

## Delivery inventory

- **Existing file changed:** `README.md` (replaced the initial short project overview with complete setup and operating instructions).
- **New source:** `backend/app/`, `backend/seed.py`, `backend/reset_demo.py`, `backend/requirements.txt`, `backend/.env.example`; `frontend/src/` and Vite/TypeScript/npm configuration with lockfile.
- **New API/database documentation:** `backend/openapi.json`, `docs/ARCHITECTURE.md`.
- **New tests and startup tools:** `backend/tests/`, `frontend/src/tests/`, `scripts/`.
- **Presentation guide:** `docs/DEMO.md`.
- **Repository hygiene:** `.gitignore` excludes installed dependencies, environments, database-independent uploads, build products and scratch work. A `checkpoint-before-implementation` Git tag preserves the initial README-only commit.
- **AI status:** Five newly recreated setup interfaces, with no external model/API integration. No existing UI was overwritten because no previous application source existed.

The app source and documentation are saved locally in the repository. No remote push, cloud database, public deployment or paid integration was performed.
