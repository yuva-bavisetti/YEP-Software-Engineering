# Known limitations and verification boundaries

No listed verification gap is represented as a passing result. The existing application and tests were retained and extended, not rebuilt.

## Implemented but unverified in this environment

1. **Real MongoDB persistence and restart:** no running MongoDB is installed here; a direct local ping returns ServerSelectionTimeoutError. Three opt-in restart checks are explicitly skipped. The real application uses PyMongo/MongoDB, not a mock fallback. Run `scripts/verify-persistence.ps1` on the laptop.
2. **Windows startup/PowerShell execution:** scripts/instructions are provided, but this is a Linux workspace without a Windows/PowerShell runtime. Python imports, Unix shell syntax, API tests, TypeScript and production build were checked. Windows service paths and Python/Node installation must be confirmed locally.
3. **Browser/WebGL/mobile visual QA:** the managed preview relay previously failed to become ready. Component tests cover routes, controls, navigation toggles, form payloads and data rendering; pure tests cover the finishing timeline. They do not verify actual GPU rendering, real viewport appearance, native file picker/PDF viewer or touch dialogs. No screenshot evidence or browser E2E pass is claimed.
4. **Real-engine distributed/crash stress:** concurrent write rejection/retry, duplicate receipts and replay of interrupted derived views are tested with mongomock. Multi-process lease renewal under arbitrary database/network pauses has not been stress-tested with real MongoDB.

## Deliberate scope and operating limits

- **No AI processing:** all five complete setup interfaces remain available with an honest unavailable-provider state. No LLM/image generation/paid API, key or fabricated response is introduced. This is intentional, not a replacement with empty Coming Soon pages.
- **No online payments:** only Admin-verified offline receipts and append-only reversals. Quotations are not treated as revenue. Later published quotations count toward payable until rejected/revision-requested; once their work starts, those changes require a controlled Admin correction rather than silently removing charges.
- **Atomic sources plus recovery, not cross-collection ACID:** business writes are serialized using a renewable MongoDB lease. It expires after 30 seconds without renewal; another concurrent writer gets retryable 409. Derived histories/links/phases/progress/customer messages are recoverable. Audit/notification writes remain separate, and a request may fail after its source commit if the database disconnects. Inspect state/idempotency history before retrying. The architecture does not promise arbitrary failure-proof transactions or high parallel throughput.
- **MongoDB physical limits:** there is no 100-phase application cap; embedded project phases/membership still obey MongoDB's document-size limit. Large production histories would need partitioning, pagination and background reconciliation; current recovery intentionally favors a small local demo dataset. Recent activity/chat polling is simple HTTP polling.
- **Explicit public publication:** projects/photographs are private by default. Admin must publish completed projects and select verified customer-shared photos. The seed includes labelled demonstration illustrations/feedback, not claims of real client commissions. Supply your own approved photographs for a real business portfolio.
- **File bounds:** 10 MB each, structurally checked PNG/JPEG/WebP up to 20 megapixels, readable unencrypted PDFs with 1–500 pages. PDF text is not parsed to reconcile written amounts against BOQ fields. There is no malware-scanning service.
- **Local-demo authentication:** bcrypt, opaque HttpOnly session cookies, SameSite, checked expiry, backend role/project/file policies and Origin checks are implemented. Public production would additionally require HTTPS/Secure cookies, rate limiting, account verification/recovery, operational backups and monitoring. Those are future deployment work, not required paid/cloud integrations.
- **Seed interruption:** ordinary reseeding never resets data. A partially created demo request is preserved rather than silently duplicated/deleted. Use a different development database for a completely clean rehearsal, or inspect the partial record before explicitly resetting a disposable database.

## Incomplete requested code features

No remaining missing core feature is known from the final audit and passing API/component suite. Runtime/visual/integration verification above remains outstanding and must be performed before claiming a fully verified laptop demonstration. REQUIREMENTS_AUDIT.md records feature-level evidence and keeps the initial findings for comparison.
