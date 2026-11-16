# YEP presentation guide

## Prepare your Windows laptop

1. Install Python 3.12+, Node 22+ and MongoDB Community, with its local service running.
2. From the repository, run `scripts/setup.ps1`, then `scripts/verify-persistence.ps1`, then `scripts/test.ps1`. See README for execution-policy/manual alternatives.
3. Run `scripts/start.ps1`; open **http://localhost:5173**. Backend docs: **http://localhost:8000/docs**.
4. Use separate browser profiles/private windows for simultaneous roles, or sign out between roles. Cookies are shared across tabs in the same browser profile.
5. Confirm the 3D scene and mobile navigation in your browser. These visual/Windows checks were not executed in the build workspace.

All development accounts use **Demo@12345**: `customer@yep.local`, `owner@yep.local`, `manager@yep.local`, `worker@yep.local`.

Seeding never resets previous records. A separate completed sample is added without replacing the active Morgan residence. If accounts have changed passwords, the supplementary seed preserves them and explains that it cannot log in. For a clean demo without deleting anything, choose another `MONGO_DB` in `backend/.env` and seed it. Do not use the destructive reset command unless you intend to discard that exact database.

## Quick tour using seeded records

- **Public:** show the single project CTA inside the animated house; services and individual details; completed portfolio and category filters; feedback; About/process/Contact. The completed sample is explicitly marked Demo and uses locally generated illustrations.
- **Customer:** overview and current phase, request/history/inspection, milestones, gallery and Customer Chat. In **Quotations & Payments**, select **The Morgan residence**: payable ₹1,30,000, paid ₹30,000, balance ₹1,00,000. The separate completed project has its own ₹12,000 quotation. Open both-page PDFs.
- **AI:** show Design Studio, Design Assistant, Cost Estimator, Recommendations and Insights. Inputs/layouts are complete; no model is connected, no results are fabricated and original images remain unchanged.
- **Worker:** show assigned projects/current phase/duration/deadline, due tasks and manager instructions. Update an own task; upload progress in Internal Team Chat or flag a work issue. Customer Chat, quotations and finances are unavailable.
- **Manager:** only assigned projects. Review a Pending photo; approve internally or **Approve & share with customer**. Add a review note; demonstrate material shortage/update, task assignment/deadline, quality checklist and execution reports. There is no financial report or PDF access.
- **Admin:** requests/inspection, quotation drafts/revisions, phase planning, employee/customer management, service image editor, contact settings, charts/audit history, verified offline receipts and reversals. Show public portfolio controls on a completed project. Admin decides which verified photos/text/feedback become public.

## Fresh request → completion

1. Customer submits a request with property details, area, location, service, date, requirements and optional photos. It goes to Admin, not Manager.
2. Admin reviews it. Optionally request clarification; Customer responds with details/photos. Schedule and complete the initial inspection. Editing a scheduled visit retains its photos; completion locks the inspection.
3. Before inspection completion, quotation preparation returns a clear error. After completion, create a Phase 1 draft with description, mandatory duration, terms and a valid multi-page PDF (unencrypted, 1–500 pages, under 10 MB). Use direct total or BOQ/material/labour/other lines with tax/discount. Ensure the uploaded document agrees with the entered totals.
4. Publish. Customer views the quotation/PDF and accepts, rejects or requests revision. A revision creates another numbered record; previous submitted records are retained.
5. After Phase 1 acceptance, Admin creates the project and assigns a manager and dates. Duplicate conversion is rejected. Define milestones and assign workers; create phase-associated tasks.
6. Worker sees only assigned projects and own tasks. Planned phase tasks are visible but cannot be executed until the phase is active. Worker posts progress privately in Internal Chat; Customer cannot fetch its file URL yet.
7. Admin/Manager reviews evidence and approves/shares the same stored file with an accompanying update. Customer can then see it, ask a question, attach an enquiry image and receive staff replies. No direct worker/customer chat exists.
8. Admin may plan another phase before its quote is prepared. Publish that phase's quotation on the same originating request/project. Close the current phase only after its milestones/tasks are complete; activate the later phase after publishing its quotation and setting dates. A completed phase cannot be reopened.
9. Record verified offline payments as Admin; keep the same idempotency key when retrying an uncertain submission. Customer totals update from the ledger. Correct a wrong receipt with a reasoned reversal, not deletion. A negative balance is displayed as customer credit.
10. Staff verify milestone progress and optionally publish the verified update to Customer Chat. Worker evidence does not automatically change milestones.
11. Mark every phase's milestones 100%, finish its tasks and complete the phase. Record a passed final quality checklist; any failed item prevents a passed result. Then complete the project. Customer can submit feedback.
12. On the completed project, Admin opens **Public Portfolio**, selects only approved/customer-shared photos, writes public text/category and chooses whether to show feedback. Publish, then check the public Projects page. Unpublishing removes public image access.

## Permission checks to show

Switch roles and demonstrate that managers/workers cannot open quote PDFs or finance URLs; workers cannot read Customer Chat; customers cannot read Internal Chat; unrelated users cannot read the project. These are backend denials, not merely hidden controls.

## Persistence rehearsal

Run `scripts/verify-persistence.ps1` against the real local MongoDB before your presentation. Then create a message/payment, stop/restart the app terminal windows, and confirm records/files remain. Keep the MongoDB service and configured upload directory intact. The automated probe restarts backend processes; it does not restart your MongoDB Windows service or test abrupt disk/power failure.

For the final manual check: desktop/mobile navigation, WebGL/fallback/reduced motion, real file pickers, PDF viewer, dialogs, four logins, the full fresh workflow and restart. Record failures honestly; do not substitute a mock database to claim persistence.
