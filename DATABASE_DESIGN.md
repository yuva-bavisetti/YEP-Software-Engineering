# MongoDB data design

The application uses MongoDB through PyMongo. There is no SQLite/Prisma layer, cloud database or in-memory runtime fallback. Mongomock is confined to isolated automated tests. Database selection and local uploads are configured in `backend/.env`.

All application records use UUID `id` fields and ISO UTC creation timestamps; MongoDB `_id` is never returned through normal DTOs. The lease/settings singletons use MongoDB's unique `_id`. Relationships are enforced in backend business logic and indexed where queried. Existing records are preserved; embedded forms represent the same logical entities without requiring separate collections for every relationship.

| Logical entity | Physical representation | References / constraints |
|---|---|---|
| Users/customer/employee profiles | `users` | Unique email; bcrypt hash; role/activation; profile fields. No API self-elevation. |
| Sessions | `sessions` | Unique opaque token hash, user ID, checked expiry; logout revocation. |
| Services | `services` | Name/description/active and optional Admin-owned image ID. |
| Project requests | `requests` | Customer ID, service/property details, photos, append-only review/lifecycle history. Customer index. |
| Inspections | `inspections` | Unique request ID; Admin actor, schedule, measurements/materials/notes/photos; completion immutable. |
| Projects | `projects` | Unique originating request; accepted Phase 1; customer/manager/worker membership; status/history/dates. Manager/worker indexes. |
| Phases | `projects.phases[]` | Distinct positive phase number per project, title, duration, dates/status, associated quote ID. Atomic guarded append; no 100-phase count cap. |
| Quotations/revisions/BOQ | `quotes` | Unique `(request_id,phase,revision)`; project/customer; status/timestamps/PDF/duration; line-item quantities as decimal strings and prices/totals as integer paise. Project index. |
| Attachments | `files` plus local files | UUID filename, owner, original name, detected type, size, extension. Owner index. Linked access resolved on every download. |
| Manager/worker assignments | project membership fields | One manager, deduplicated worker IDs. Current membership is authoritative. |
| Milestones | `milestones` | Project + phase; definition/deadline; verified progress, status/updater/time; durable optional publication metadata. |
| Tasks/assignments | `tasks` | Project + phase + worker; title/instructions/deadline/priority/status. Worker index. |
| Progress submissions/verification | internal `messages` | Photo + Pending/Approved/Rejected; reviewer/time/note. Source file is reused when shared. |
| Two chats | `projects.channels` + `messages.channel` | Exactly `internal` and `customer`; no direct or third chat creation API. |
| Messages/project updates | `messages` | Project/channel/sender/text/image/issue; indexed project/channel/time. Unique sparse source ID and deterministic publication IDs. |
| Materials/shortages | `materials` | Project, material quantity/unit/status/notes and updating staff. No financial fields. |
| Quality/checklist/defects | `quality` | Project, named inspection, structured passed flags, defects/corrective action and staff actor. |
| Notifications | `notifications` | Scoped user event, read state, timestamp. Only owner can mark read. |
| Offline payments/reversals | `payments` | Project, integer paise, method/reference/date/verification/actor; unique project/idempotency key. Reversal references original entry; no deletion. |
| Audit history | `activity` | Append-only actor/action/target/time. No password/session secrets returned. |
| Customer feedback | `feedback` | Unique project/customer pair; completed projects only. |
| Public completed portfolio | `portfolio` | Unique project ID; public title/description/category and selected verified file IDs; published flag; optional feedback. |
| Contact enquiries | `enquiries` | Public name/email/phone/message; Admin-only read access. |
| Business contact settings | `settings` singleton | Only selected public contact fields returned publicly; Admin-only edit. |
| Business-write lease | `workflow_locks` singleton | Atomic unique `_id`, owner token, renewable expiry; serializes business writes across local API processes. |

`init_indexes()` runs on startup/seed. No seed or ordinary startup drops a collection. The explicit development reset command requires the exact configured database name and is restricted to `yep*` databases. It retains old uploaded files. For a fresh presentation without touching previous data, choose a new `MONGO_DB` and seed it.

## Financial derivation

Current payable = accepted initial quotation + published/accepted later phase quotations; rejected/draft/revision-requested records are not added. Revision history is not counted twice. Paid = positive verified receipts plus negative reversal records. Balance = payable − paid; a negative balance is customer credit. Neither quoted value nor an unverified receipt is called earned revenue.

## Recovery / integrity

Source records are atomic, phase decisions use conditional updates, unique keys guard repeated conversions/receipts/revisions, and a renewable DB lease serializes business mutations. Recovery replays derived links, statuses/history, phase publications, progress and verified milestone messages. It does not erase source data. See ARCHITECTURE.md for the explicit distinction between this standalone-MongoDB design and replica-set multi-document transactions.

## Actual persistence verification

Run `scripts/verify-persistence.ps1` with local MongoDB running. It uses uniquely named `yep_test_*` databases and exercises actual writes and backend restarts. These tests are **not** considered passed when skipped or run with mongomock. No running MongoDB was available in this build environment.
