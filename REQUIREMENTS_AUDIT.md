# YEP requirements audit

Baseline inspected: commit `485caca` (all 49 tracked files, 60 API operations, Pydantic models, permission policies, React components/forms, scripts and tests). Final Admin-led workflow takes precedence. This is an evidence checklist, not a claim that rendering proves functionality. Runtime/browser/Windows verification is tracked separately.

Labels: **COMPLETE AND TESTED**, **IMPLEMENTED BUT UNTESTED**, **PARTIALLY IMPLEMENTED**, **MISSING**, **BROKEN**. Baseline classifications below are preserved; a final status/evidence table will be appended after implementation.

| Requirement | Baseline classification | Inspection / existing evidence |
|---|---|---|
| React/TypeScript/Tailwind/FastAPI/MongoDB/local uploads | COMPLETE AND TESTED | Build, API and component suites; real MongoDB remains separate |
| Four role logins and bcrypt/opaque cookie sessions | COMPLETE AND TESTED | API fixture authenticates all roles; role dashboard tests |
| Registration and duplicate email validation | PARTIALLY IMPLEMENTED | Implemented; successful registration/duplicate/production protections need tests |
| Role-scoped requests/projects/tasks/chats/files | COMPLETE AND TESTED | Workflow/permission tests; broaden cross-project matrix |
| Homepage, About, process and Contact layouts | COMPLETE AND TESTED | Six public routes covered by DOM tests; not browser rendering |
| Contact enquiry persistence and Admin display | IMPLEMENTED BUT UNTESTED | `/api/enquiries`, Admin customer/enquiry panel |
| Nine services seeded and selectable | PARTIALLY IMPLEMENTED | Seed/API; no explicit all-nine acceptance check |
| Service detail pages use saved descriptions/stable links | PARTIALLY IMPLEMENTED | Indexed routes and generic text ignore saved descriptions |
| Service imagery management | MISSING | No image field/public service asset route |
| Completed project gallery/category filters | MISSING | Existing gallery is labelled concept studies, not completed database projects |
| Testimonials from real feedback | MISSING | Feedback stored privately; no approved public portfolio flow |
| Responsive navigation/mobile layout | IMPLEMENTED BUT UNTESTED | CSS and toggles present; viewport/browser behavior unverified |
| 3D unfinished→finished doors/windows/landscape | PARTIALLY IMPLEMENTED | Walls change tone, remaining materials static; WebGL unverified |
| Single prominent hero CTA and preserved login destination | PARTIALLY IMPLEMENTED | Implemented; destination regression test missing |
| Customer overview/project/request/quotation statistics | PARTIALLY IMPLEMENTED | Client derives counts from scoped MongoDB lists; dedicated stats/activity endpoint missing |
| Request property inputs and photographs → Admin only | COMPLETE AND TESTED | Full API and form payload tests |
| Request history, Admin clarification and response | PARTIALLY IMPLEMENTED | Clarification history exists; inspection/quote/project lifecycle history incomplete |
| Inspection scheduling/measurements/materials/photos | COMPLETE AND TESTED | Admin-only inspection API and workflow tests |
| Safe updates to scheduled inspection/photo retention | PARTIALLY IMPLEMENTED | Resubmission replaces attachment array; reuse check rejects retained photos |
| Initial inspection gates draft/publication | COMPLETE AND TESTED | API tests |
| BOQ totals, tax/discount, PDF/duration, revisions | COMPLETE AND TESTED | BOQ/API and exact frontend arithmetic tests |
| Revision accounting and overpayment regression | PARTIALLY IMPLEMENTED | Calculation implemented; expanded accounting tests missing |
| Initial acceptance/unique project creation | COMPLETE AND TESTED | Conditional decision and unique originating request |
| Phases with mandatory duration, dates and quote | PARTIALLY IMPLEMENTED | Published quotations create phases; hard phase cap 100; blank later schedules |
| Valid phase status/date/order transitions | MISSING | Any phase status can be selected without transition validation |
| Admin manager assignment / manager worker assignment | COMPLETE AND TESTED | Scope/assignment tests |
| Manager/worker current phase and deadlines | PARTIALLY IMPLEMENTED | All phases displayed, no explicit current-phase summary |
| Milestone definitions/progress/deadlines/last updater | PARTIALLY IMPLEMENTED | Edit APIs exist; UI only deadline edit; status derived only in UI |
| Customer verified milestone notifications/chat updates | PARTIALLY IMPLEMENTED | Verified progress shown; no published milestone chat event |
| Project progress/completion consistency | PARTIALLY IMPLEMENTED | Stored rounded average can reach 100 before every milestone is complete |
| Task creation/reassignment/status/deadlines | COMPLETE AND TESTED | Task assignment/deadline permission tests |
| Completed task/project mutation prevention | PARTIALLY IMPLEMENTED | Executor guards exist; worker task-status endpoint lacks completion guard |
| Materials/shortages tracking | PARTIALLY IMPLEMENTED | Add/list only; cannot update availability/resolve shortage |
| Quality inspections/defects/corrective actions | COMPLETE AND TESTED | Completion gate tests; broaden failed-quality cases |
| Manager nonfinancial reports | MISSING | Admin financial reports only |
| Worker today tasks/instructions/issues summary | PARTIALLY IMPLEMENTED | Project task/chat inputs exist; dedicated overview missing |
| Exactly two persistent group chats | COMPLETE AND TESTED | Membership, channel validation, no DM endpoint |
| Pending worker photos/verification/share existing image | COMPLETE AND TESTED | API isolation and direct-file tests |
| Reject reason and approve-now/share-later UI | PARTIALLY IMPLEMENTED | Backend share endpoint exists; only combined share control in UI |
| Customer enquiry image/text and staff responses | COMPLETE AND TESTED | Workflow test |
| Quotation/payment/PDF privacy | COMPLETE AND TESTED | Role/customer ownership and direct-file restrictions |
| Offline instalments/idempotency/reversal audit | COMPLETE AND TESTED | Workflow tests |
| Finance progress/credit presentation | PARTIALLY IMPLEMENTED | Correct raw totals; no paid percentage or explicit credit label |
| Employee add/edit/activate and customer management | IMPLEMENTED BUT UNTESTED | APIs/forms exist; need CRUD/role/privacy regression tests |
| Service add/edit/deactivate | IMPLEMENTED BUT UNTESTED | APIs/forms exist; API coverage missing |
| Admin analytics/activity | PARTIALLY IMPLEMENTED | Four charts exist; missing monthly project activity/quotation distribution |
| Notifications marking read | PARTIALLY IMPLEMENTED | Backend read endpoint exists; no UI action/polling for general updates |
| Profile name/email/phone/address/password | IMPLEMENTED BUT UNTESTED | Forms/APIs; regression tests missing |
| All five AI setup interfaces/no fabricated outputs | COMPLETE AND TESTED | DOM tests, no provider calls; assistant named AI Assistant |
| Strict schema/IDs/local file metadata and safe downloads | PARTIALLY IMPLEMENTED | Signature/size/ownership validation; malformed/truncated assets accepted |
| Atomic multi-step updates/recovery | PARTIALLY IMPLEMENTED | Conditional updates/unique keys, photo recovery; other derived updates have crash gaps |
| Local MongoDB persistence/restart | IMPLEMENTED BUT UNTESTED | Opt-in real-engine restart test; no MongoDB server in workspace |
| Windows setup/start/reset/seed/demo accounts | IMPLEMENTED BUT UNTESTED | PowerShell code/docs exist; Windows unavailable |
| Repeatable non-destructive seed | COMPLETE AND TESTED | Existing seed repeatability test |
| 42 acceptance scenarios explicitly mapped | MISSING | Many covered by aggregate test; no complete traceability matrix |
| Required root delivery documents | PARTIALLY IMPLEMENTED | README and docs/ exist; root audit/API/database/demo/results/limits missing |

No existing application was reset or reconstructed. Baseline code is preserved in Git. Browser/WebGL, Windows and real MongoDB are never labelled passed based on substitutes.
