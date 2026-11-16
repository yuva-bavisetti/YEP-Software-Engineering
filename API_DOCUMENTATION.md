# API documentation

Generated from the actual FastAPI OpenAPI schema. Interactive documentation: `http://localhost:8000/docs`. Full field constraints and JSON schemas: `backend/openapi.json` or `/openapi.json`.

Authentication uses the HttpOnly `yep_session` cookie. Login first; the local browser retains it. All permission checks run on the backend. State-changing authenticated requests reject foreign Origin headers. Body schemas forbid unexpected fields. Files are multipart; other mutations use JSON.

## Responses

- 401: sign in / invalid credentials.
- 403: role/project/chat/file policy denies access.
- 404: missing or intentionally hidden record/asset.
- 409: duplicate/invalid state, immutable/completed execution, or concurrent writer (retry after existing write finishes).
- 422: field, file, date, amount, duration, BOQ or transition input invalid.
- 503: local MongoDB unavailable.

## Permissions

Public: auth registration/login, active services/images, public contact settings, published completed portfolio/selected photos, enquiry submission, health. Admin: initial inspections/quotation creation/publication, project creation/manager assignment, finance writes, employees/services/settings/publication. Admin + respective customer: quotations/PDFs/finances. Admin + assigned manager: execution management/reports. Worker: assigned project/current phase/milestones, own task updates, internal chat only. Customer: own data, customer chat only. All protected downloads independently resolve their linked authorization.

## Endpoints

| Method | Path | Operation |
|---|---|---|
| GET | `/api/health` | Health |
| POST | `/api/auth/register` | Register |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Me |
| GET | `/api/services` | Services |
| POST | `/api/services` | Add Service |
| POST | `/api/enquiries` | Enquiry |
| GET | `/api/users` | Users |
| POST | `/api/users` | Employee |
| GET | `/api/requests` | Requests |
| POST | `/api/requests` | Create Request |
| GET | `/api/requests/{rid}/inspection` | Inspection |
| POST | `/api/requests/{rid}/inspection` | Inspect |
| POST | `/api/requests/{rid}/quotes` | Create Quote |
| GET | `/api/quotes` | Quotes |
| POST | `/api/quotes/{qid}/publish` | Publish |
| POST | `/api/quotes/{qid}/decision` | Decision |
| GET | `/api/projects` | Projects |
| POST | `/api/projects` | Create Project |
| POST | `/api/projects/{pid}/workers` | Assign |
| GET | `/api/projects/{pid}/milestones` | Milestones |
| POST | `/api/projects/{pid}/milestones` | Milestone |
| PATCH | `/api/milestones/{mid}` | Progress |
| PUT | `/api/milestones/{mid}` | Edit Milestone |
| POST | `/api/projects/{pid}/complete` | Complete |
| GET | `/api/projects/{pid}/tasks` | Tasks |
| POST | `/api/projects/{pid}/tasks` | Task |
| PATCH | `/api/tasks/{tid}` | Task Status |
| PUT | `/api/tasks/{tid}` | Edit Task |
| GET | `/api/projects/{pid}/chat/{channel}` | Messages |
| POST | `/api/projects/{pid}/chat/{channel}` | Message |
| POST | `/api/messages/{mid}/verify` | Verify |
| GET | `/api/projects/{pid}/finance` | Finance |
| POST | `/api/projects/{pid}/payments` | Payment |
| POST | `/api/payments/{payment_id}/reverse` | Reverse |
| POST | `/api/files` | Upload |
| GET | `/api/files/{fid}` | Download |
| GET | `/api/notifications` | Notifications |
| GET | `/api/activity` | Activity |
| PATCH | `/api/profile` | Profile |
| PATCH | `/api/users/{uid}/active` | Activate |
| POST | `/api/projects/{pid}/feedback` | Feedback |
| PATCH | `/api/projects/{pid}/phases/{number}` | Phase Update |
| PATCH | `/api/projects/{pid}/manager` | Reassign |
| PUT | `/api/services/{sid}` | Edit Service |
| PATCH | `/api/requests/{rid}/status` | Request Status |
| GET | `/api/projects/{pid}/materials` | Materials |
| POST | `/api/projects/{pid}/materials` | Material |
| GET | `/api/projects/{pid}/quality` | Quality |
| POST | `/api/projects/{pid}/quality` | Quality Record |
| GET | `/api/admin/summary` | Admin Summary |
| GET | `/api/admin/customers` | Customers |
| GET | `/api/admin/enquiries` | Enquiries |
| GET | `/api/admin/services` | Admin Services |
| PATCH | `/api/notifications/{nid}/read` | Read Notification |
| POST | `/api/messages/{mid}/share` | Share Approved |
| POST | `/api/requests/{rid}/reply` | Request Reply |
| PUT | `/api/quotes/{qid}` | Edit Draft |
| PATCH | `/api/users/{uid}` | Employee Details |
| GET | `/api/dashboard` | Dashboard |
| GET | `/api/reports` | Reports |
| PUT | `/api/materials/{mid}` | Edit Material |
| PATCH | `/api/projects/{pid}/status` | Status |
| GET | `/api/public/projects` | Portfolio |
| GET | `/api/projects/{pid}/portfolio` | Portfolio Settings |
| PUT | `/api/projects/{pid}/portfolio` | Publish Portfolio |
| GET | `/api/public/projects/{pid}/photos/{fid}` | Portfolio Photo |
| GET | `/api/public/services/{sid}/image` | Service Image |
| POST | `/api/projects/{pid}/phases` | Plan Phase |
| GET | `/api/admin/customers/{uid}/history` | Customer History |
| GET | `/api/settings/public` | Public Settings |
| PUT | `/api/admin/settings` | Update Settings |

## Important payloads

- Request: service, property type/location/area/rooms/description, preferred date/requirements, local photo IDs.
- Inspection: date, measurements, notes/materials, completed flag and image IDs. Retained inspection photos need not be uploaded again.
- Quotation: phase/title/description, amount, mandatory duration, PDF ID, terms and optional BOQ/tax/discount. Draft edit retains phase/revision; later revisions create new records.
- Project: accepted initial quote ID, title, assigned manager, start/deadline. Converts one request once.
- Phase planning: number/title/duration, optional paired dates. Activation requires an official published quotation and completed earlier phases.
- Task: project-associated phase, worker, title/instructions/deadline/priority. Reassignment preserves phase.
- Milestone: title/description/phase/deadline; verified progress updates can explicitly publish a customer-chat update.
- Evidence: internal image message → staff verification (approve/reject/note) → optional share with text. The same file ID is referenced.
- Receipt: amount/date/method/reference/notes, offline verification information and stable idempotency key. A correction posts a negative reversal with a reason.
- Portfolio: completed project, public title/description/category, selected verified/customer-shared file IDs, published/show-feedback flags.
- Service: name/description/active and optional uploaded image ID.
- Employee edit: name/email/phone, optional Manager/Worker role. Changing duties requires reassignment of active projects first.

## File limits

Images: structurally validated PNG/JPEG/WebP, at most 20 megapixels. PDFs: readable, unencrypted, 1–500 pages. Every file: at most 10 MB. Only Admin uploads PDFs; chat attachments are images. No generic public mount of uploads exists. Public service/portfolio assets require explicit active publication.

No API integrates an AI provider or an online payment gateway.
