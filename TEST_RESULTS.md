# Final automated verification results

Executed in the Linux workspace on 16 November 2026 (Python 3.12.14, Node 24.22.1). No failures remain in the completed test runs.

| Check | Result | Evidence / limits |
|---|---|---|
| Backend suite | **65 passed, 3 skipped, 0 failures** | FastAPI handlers and database operations against isolated mongomock databases; JUnit generated during the run |
| 42 acceptance scenarios | **40 passed, 2 skipped** | Named matrix below; real MongoDB restart scenarios explicitly skipped |
| Additional API regressions | **25 passed** | Original 9 preserved/extended plus 16 audit regressions |
| Frontend component/unit suite | **34 passed, 0 failures** | 3 Vitest suites, jsdom/API substitutes; no real GPU/browser claims |
| TypeScript + production build | **Passed** | `npm run build`; lazy Three.js chunk; no build errors |
| Python source compilation | **Passed** | `python -m compileall -q backend` |
| Unix scripts | **Syntax passed** | `bash -n scripts/setup.sh scripts/start.sh` |
| OpenAPI export | **Passed** | Actual registered API/model specification regenerated in backend/openapi.json and API_DOCUMENTATION.md |
| Actual local MongoDB ping | **Unavailable** | ServerSelectionTimeoutError; no running local MongoDB |
| Windows/PowerShell execution | **Not executed** | Linux environment; scripts and laptop commands provided |
| Browser/WebGL/mobile visual QA | **Not executed** | Managed preview relay unavailable; DOM/timeline tests are narrower evidence |

One dependency-level AnyIO/Starlette TestClient deprecation warning remains. It is not an application failure. The source was not reset or regenerated; existing tests were retained and expanded where stricter phase/asset validation changed expected inputs.

## All 42 acceptance scenarios

The backend matrix runs one complete real API-handler journey through isolated database records, then asserts each recorded scenario separately. It is not 42 separate browser sessions. Cases 38–41 additionally rely on the corresponding frontend component suite; backend/static checks alone do not establish browser rendering.

| # | Scenario | Result | Verification layer |
|---|---|---|---|
| 1 | Customer logs in | PASSED | Actual API handlers + isolated database |
| 2 | Customer submits request | PASSED | Actual API handlers + isolated database |
| 3 | Admin receives request | PASSED | Actual API handlers + isolated database |
| 4 | Manager cannot receive unassigned request | PASSED | Actual API handlers + isolated database |
| 5 | Admin completes inspection | PASSED | Actual API handlers + isolated database |
| 6 | Inspection required before quotation | PASSED | Actual API handlers + isolated database |
| 7 | Admin uploads Phase 1 PDF | PASSED | Actual API handlers + isolated database |
| 8 | Duration mandatory | PASSED | Actual API handlers + isolated database |
| 9 | Customer views quotation | PASSED | Actual API handlers + isolated database |
| 10 | Customer accepts Phase 1 | PASSED | Actual API handlers + isolated database |
| 11 | Admin creates project | PASSED | Actual API handlers + isolated database |
| 12 | Admin creates milestones | PASSED | Actual API handlers + isolated database |
| 13 | Admin assigns Manager | PASSED | Actual API handlers + isolated database |
| 14 | Assigned Manager sees project | PASSED | Actual API handlers + isolated database |
| 15 | Manager assigns Workers | PASSED | Actual API handlers + isolated database |
| 16 | Workers see project and milestones | PASSED | Actual API handlers + isolated database |
| 17 | Worker sees current phase and duration | PASSED | Actual API handlers + isolated database |
| 18 | Worker uploads internal progress photo | PASSED | Actual API handlers + isolated database |
| 19 | Photo initially Pending | PASSED | Actual API handlers + isolated database |
| 20 | Unverified photo hidden from Customer | PASSED | Actual API handlers + isolated database |
| 21 | Manager approves evidence | PASSED | Actual API handlers + isolated database |
| 22 | Verified photo shared without new upload | PASSED | Actual API handlers + isolated database |
| 23 | Customer views published progress | PASSED | Actual API handlers + isolated database |
| 24 | Customer sends query image and text | PASSED | Actual API handlers + isolated database |
| 25 | Admin and Manager respond | PASSED | Actual API handlers + isolated database |
| 26 | Admin creates subsequent quotation | PASSED | Actual API handlers + isolated database |
| 27 | Later phase belongs to same project | PASSED | Actual API handlers + isolated database |
| 28 | Customer sees phase quotation history | PASSED | Actual API handlers + isolated database |
| 29 | Admin records offline payment | PASSED | Actual API handlers + isolated database |
| 30 | Customer payable paid balance correct | PASSED | Actual API handlers + isolated database |
| 31 | Manager financial access denied | PASSED | Actual API handlers + isolated database |
| 32 | Worker financial access denied | PASSED | Actual API handlers + isolated database |
| 33 | Worker Customer Chat access denied | PASSED | Actual API handlers + isolated database |
| 34 | Customer Internal Chat access denied | PASSED | Actual API handlers + isolated database |
| 35 | Unassigned users cannot access project | PASSED | Actual API handlers + isolated database |
| 36 | Chat survives backend restart with MongoDB | SKIPPED | Real MongoDB/backend-process restart required |
| 37 | Payment and quotation survive backend restart | SKIPPED | Real MongoDB/backend-process restart required |
| 38 | Four dashboard APIs load | PASSED | API + component suite |
| 39 | Public data and page routing available | PASSED | API + component suite |
| 40 | Five AI navigation and setup interfaces remain | PASSED | API + component suite |
| 41 | AI screens not replaced with placeholders | PASSED | API + component suite |
| 42 | No external AI integration introduced | PASSED | Source/provider-boundary + component checks |

## Additional regression coverage

Successful registration/duplicate email; profile/email/password changes; logout; forbidden elevation; employee add/edit/activation/role changes; optional role retention; staff directory privacy; service editing/deactivation/managed image access; public enquiry/contact settings; customer project history; scheduled photo retention; lifecycle history; unbounded planned phase numbering; phase activation/order/immutability; no execution of planned tasks; revision accounting without double counting; negative payments/overpayments/reversals; correct paid/balance arithmetic; material shortage resolution; quality checklist/defect validation; scoped reports and database statistics; renewable write-lease contention/expired recovery; simultaneous duplicate receipt submissions; recovery of interrupted project/quote/phase/progress views; malformed/oversize/private files; cross-project isolation; completed execution guards; exact milestone completion checks; verified milestone chat publication; read-notification ownership; Admin on-hold/resume; explicit public publication/unpublication and selected approved photo privacy; actionable MongoDB errors; non-destructive completed/active demo seed.

Frontend checks cover all role dashboards; six public routes; mobile-menu control state; saved service descriptions/images; completed category filters; registration destination handoff; customer request and inspection payloads; file input collection; selected task phase; phase scheduling defaults/planning; structured quality checklists; public portfolio controls; scoped reports/worker instructions; contact settings; service uploads; finance presentation; notification reads; preserved AI screens/no processing; exact currency rounding; finishing timeline and reduced-motion behavior.

## Execute on Windows against actual MongoDB

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-persistence.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\test.ps1
```

The persistence script honors an explicitly set MONGO_TEST_URL; otherwise it reads the backend .env MongoDB URI (environment variables take precedence). Its test databases are unique `yep_test_*` names, removed afterwards. It does not reset the demo database or stop/restart the MongoDB service.

The suite can also be run manually:

```powershell
$env:MONGO_TEST_URL = 'mongodb://127.0.0.1:27017'
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npm --prefix frontend test
npm --prefix frontend run build
```

Three skipped checks consist of acceptance scenarios 36/37 and the standalone sessions/files/chat/payment/quotation backend-restart probe. They must run against a real server before disk persistence is called verified. The acceptance restart probe starts and restarts a backend process against the actual journey's database; it does not restart the MongoDB engine itself.

See DEMO_GUIDE.md for the final browser/Windows/3D manual rehearsal. KNOWN_LIMITATIONS.md explicitly separates intentional AI/payment scope from unverified runtime properties.
