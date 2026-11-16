> Baseline document retained from the initial implementation. For current behavior and verification, read [ARCHITECTURE.md](../ARCHITECTURE.md).

# Architecture and security

YEP is a modular monolith: one React/Vite client, one FastAPI application, one local MongoDB database and one private local upload directory. Backend routes orchestrate workflow logic; validation and authorization are independent modules. No microservices or cloud storage are required.

## MongoDB document relationships

All records have application UUID `id` values and creation timestamps. MongoDB `_id`, password hashes and session token hashes are excluded from API responses.

| Collection | Ownership and relationships |
|---|---|
| users | Unique normalized email, role, bcrypt hash, active flag and profile |
| sessions | Unique SHA-256 token hash, user ID, checked expiration |
| requests | Customer ID, property/service details, attachment IDs, review history |
| inspections | Unique request ID, Admin ID, completed flag, measurements/material notes |
| quotes | Request/customer/project IDs, phase/revision, immutable published content, PDF ID, BOQ/totals/duration, decision timestamp |
| projects | Unique request ID, accepted initial quote, customer/manager/worker IDs, embedded phases and exactly two channel names |
| milestones | Project ID, phase number, deadline, verified progress, updater |
| tasks | Project ID, worker ID, instructions, priority, deadline and status |
| messages | Project ID and channel; sender; image ID; verification metadata; customer shares reference their source |
| files | Owner, original name, byte size, detected type and private disk extension |
| payments | Project ID, integer paise, offline verifier, method/reference/date, idempotency key; negative reversal references the original |
| materials | Project ID, quantity/unit, availability or shortage, notes |
| quality | Project ID, checklist/area, pass/fail, defects/corrective action, reviewer |
| notifications | Recipient ID, safe event text, timestamp |
| feedback | Unique project/customer pair, rating and feedback |
| services | Active service catalogue and descriptions |
| enquiries | Public contact form submissions, visible only to Admin |
| activity | Actor, operation, target and timestamp; no financial body is copied into execution chats |

Indexes enforce unique email/session tokens, one project per request, one inspection per request, distinct phase revisions, per-project payment idempotency, one published share per photo source, and one feedback record per project/customer. Task worker IDs, file owners and project/channel/message order are indexed. MongoDB is schemaless at the storage layer; application writes are validated with Pydantic. Direct database edits are outside these guarantees.

## Access matrix

| Operation | Customer | Admin | Assigned manager | Assigned worker |
|---|---|---|---|---|
| Requests / initial inspections | Own records, reply to clarification | Review and inspect | No | No |
| Quotations and quotation PDFs | Own published/history, decisions | Create/edit drafts/publish/revise | No | No |
| Create project / assign manager | No | Yes, after Phase 1 acceptance | No | No |
| Project/phase schedule | View own | Manage | Manage execution on assigned projects | View assigned |
| Assign workers / create tasks | No | Yes | Assigned project only | No |
| Milestone changes | View verified | Yes | Assigned project only | No |
| Task status | View | Yes | Assigned project only | Own assigned tasks only |
| Internal chat/photos | No | Yes | Assigned project only | Assigned project only |
| Verify/share progress | No | Yes | Assigned project only | No |
| Customer chat/photos | Own project only | Yes | Assigned project only | No |
| Quotations / finance / offline payments | Own read-only | All; append/reverse receipts | No | No |
| Employee/service/admin reporting | No | Yes | Only execution staff directory | No |

All restrictions run on the server. Project list DTOs remove initial quotation references and phase quotation IDs from managers/workers; workers also do not receive customer identity fields. The execution interface contains phase durations and dates but no monetary data. Users cannot fetch another worker's task records or a project's data merely by guessing IDs.

There is no static mount for uploads. Every file download resolves its linked request, inspection, quote or authorized chat message. A customer cannot download an internal photo until a verified customer share exists. PDFs can only be uploaded by Admin and cannot be attached to chats. Message image uploads are checked for ownership and detected image format. Unlinked uploads are private to the uploader. Files are capped at 10 MB and accept PDF/PNG/JPEG/WebP signatures; this is format filtering, not a malware scanner or full document parser.

Sessions use cryptographically random opaque tokens, stored as hashes, with HttpOnly/SameSite cookies, expiry checks and logout revocation. Production HTTPS can enable Secure cookies. State-changing authenticated requests reject foreign Origin headers. Clients cannot set their own role during registration. Deactivated accounts are denied even with an existing cookie. Demo credentials are intentionally documented for localhost use.

## State and consistency

- Inspection completion gates quotation preparation and publication. A completed inspection is immutable.
- Draft quotations can be edited. Published → Accepted / Rejected / Revision Requested is a conditional atomic update; duplicate decisions return 409. Rejected/revision-requested quotations allow a new numbered revision while retaining history.
- Phase 1 must be Accepted to create a project. A unique request index prevents duplicate projects even under concurrent submissions. Worker assignment uses `$addToSet`.
- Projects embed their two channels and phases. No API exists to create additional conversations.
- Progress verification uses a conditional Pending → Approved/Rejected update. Approved sharing retains reviewer/time/source and reuses the same stored image. Deterministic customer share IDs and a unique source index prevent duplicate sharing. Customer-chat reads can reconstruct an interrupted approved share from its durable publication metadata.
- Money uses Decimal validation and half-up conversion to integer paise. BOQ extensions, taxes, discount and the submitted grand total are validated on the server. Payments are append-only, uniquely keyed by project/idempotency key; a reversal is a separately keyed negative entry. Financial summaries derive from current quote/payment records, not client-provided totals.
- All phases and milestones must finish, tasks must finish, and the latest quality review must pass before completion. Completed project execution is read-only; historical chats, finances and feedback remain available as permitted.

**Failure boundaries:** This version uses standalone MongoDB-compatible atomic document updates and unique indexes, not cross-collection MongoDB transactions. Audit/notification writes and some linked project/quotation/milestone updates are separate writes. A process/database interruption between them can leave a missing notification/audit entry, an unlinked quotation project field, a stale aggregate progress value or an incomplete phase publication. Photo-share reconstruction covers that specific interrupted operation. For a production deployment, add a transactional outbox or replica-set transactions and recovery jobs before promising all-or-nothing multi-document updates. The presentation's normal single-user workflow is tested; crash/concurrency fault injection has not been performed.

## Frontend

A shared responsive shell renders role-specific navigation. The server remains authoritative; hidden controls are not the security boundary. The public website and dashboard features use reusable typed form controls and a cookie-aware API client. Three.js is loaded separately so it does not block dashboard code. System fonts and procedural/local illustrations keep the app usable offline after dependencies have been installed.

AI feature modules are strictly interface setup screens. No model-specific implementation, API keys, generated responses or paid provider dependencies exist. Input widgets can later be wired to independent adapters.

## API groups

- `/api/auth/*`: register, login, logout, current user
- `/api/profile`: profile/password update
- `/api/services`, `/api/enquiries`: public catalogue and enquiry submission
- `/api/requests/*`: customer creation/list, Admin review/inspection/quotation, customer clarification
- `/api/quotes/*`: permitted listing, draft editing, Admin publish, customer decision
- `/api/projects/*`: create/list, phases, manager/worker assignment, milestones/tasks/materials/quality, chats, finance/payments, completion/feedback
- `/api/milestones/*`, `/api/tasks/*`: protected execution updates
- `/api/messages/*`: verification/customer publishing
- `/api/payments/*/reverse`: Admin audit-preserving correction
- `/api/files/*`: authenticated uploads and downloads
- `/api/admin/*`, `/api/users/*`, `/api/activity`: permitted administrative management/reporting
- `/api/notifications`, `/api/health`: recipient events and database health

The generated `/docs` page is the detailed request/response contract; native FastAPI 401/403/404/409/422/503 responses surface meaningful failures in the UI.

## Collections

| Collection | References / purpose |
|---|---|
| `users` | Name/email/phone/address, role, active state, bcrypt password hash; unique email |
| `sessions` | User ID, hashed opaque token and expiry; unique token hash |
| `services` | Public active catalogue; Admin-managed description and activation |
| `requests` | Customer ID, property/service details, private file IDs and review/clarification history |
| `inspections` | Unique request ID, Admin ID, schedule, measurements, findings, materials and photos |
| `quotes` | Request/customer/project IDs, phase/revision unique key, structured amount/BOQ, PDF, duration, terms and decision timestamps |
| `projects` | Unique originating request, accepted Phase 1, customer, manager, deduplicated workers, embedded phases and exactly two channel names |
| `milestones` | Project/phase, definition/deadline, verified progress, updating user and time |
| `tasks` | Project and assigned worker, instructions, deadline, priority and state |
| `messages` | Project/channel, sender, body, private image reference, verification and optional original source ID |
| `files` | UUID, owner, original display name, detected format, extension, byte size; disk path is generated from UUID |
| `materials` | Project, quantity/unit, required/available/shortage state and notes |
| `quality` | Project, checklist/area, result, defects/corrective action and reviewer |
| `payments` | Project, integer amount, method/date/reference, offline verification, idempotency key and reversal reference |
| `notifications` | User-scoped event text and timestamp |
| `feedback` | Unique project/customer pair, rating/text after completion |
| `activity` | Append-only actor/action/target audit history |
| `enquiries` | General public contact messages available to Admin |

MongoDB creates collections on first write. `init_indexes()` creates/updates indexes on startup and seeding. Application validation enforces references and transitions; there is no SQL/Prisma migration layer in this MongoDB implementation. Existing records are not erased by index creation or seeding.
