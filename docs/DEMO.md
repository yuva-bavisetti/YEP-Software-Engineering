# University presentation walkthrough

Start MongoDB, run setup and start both servers. Use separate browser profiles/private windows for simultaneous roles, or sign out before changing accounts. Cookies are intentionally shared by tabs on the same browser profile.

## Existing sample project (quick demonstration)

1. Open `http://localhost:5173`. Show the procedural animated house and service/process pages. Use **Log in**.
2. Customer `customer@yep.local` / `Demo@12345`: show the request, active project and verified milestone progress. Open **Quotations & Payments**: Phase 1 accepted, Phase 2 published, two-page PDFs, ₹1,30,000 payable / ₹30,000 paid / ₹1,00,000 balance.
3. Open **Projects → View project → Customer Project Chat**. The approved illustration is visible; the pending internal photograph is absent. Send a question and optionally attach an image.
4. Show each of the five AI interfaces. Explain they are input/setup screens with no connected AI service and do not generate results.
5. Sign in as Worker. Open assigned project, phase duration/deadline, own task and Internal Team Chat. Update task status; upload a real PNG/JPEG/WebP photograph as progress or flag a work issue. No quotations, finances or Customer Chat are available.
6. Sign in as Manager. Review Internal Team Chat and **Approve & share with customer**. Enter an accompanying update. Show the customer-facing chat and verify the same image appears. Demonstrate task assignment, milestones, materials and quality records. Quotations/finances remain unavailable.
7. Sign in as Admin. Open Requests and inspection; show quotations, team, reports, services, customers/enquiries and audit history. Record a small offline-verified instalment and show the Customer's updated totals. Explain receipt versus quotation value. If demonstrating corrections, reverse the receipt with a reason; evidence remains in history.

## Fresh end-to-end workflow

1. Customer creates a new request with property information and optional photos.
2. Admin reviews it. Attempting to prepare a quotation before inspection fails. Schedule/complete the Admin inspection.
3. Admin prepares a Phase 1 draft: title, amount or optional BOQ, duration, terms and a real multi-page PDF under 10 MB. Publish it.
4. Customer opens the PDF and accepts. Admin creates the project and chooses a manager and dates. Repeated conversion is rejected.
5. Manager sees the project only after assignment. Admin/manager adds milestones and assigns a worker; then creates that worker's tasks.
6. Worker sees the project, phase duration, deadlines and assigned tasks, posts pending evidence in Internal Chat and updates task status.
7. Manager/Admin verifies the evidence and shares it to Customer Chat. Customers cannot access its direct URL before sharing. Customer sends text/query image; Manager/Admin replies.
8. Admin returns to the original request to create Phase 2 (or later) with mandatory duration and a new PDF, then publishes it. It remains on the same project. Schedule that phase under **Phases & Team**.
9. Admin records a payment only after offline verification. Show the balance and payment history in the Customer account.
10. Complete all tasks and milestones, set every phase to Completed, and record a passed final quality inspection under **Quality**. Use **Quality passed · Complete project**. Customer can submit feedback.

## Persistence demonstration

After creating a message/payment, stop the frontend and backend windows. Leave MongoDB's persistent service/data directory intact. Restart both servers and sign in: messages, quotations, files and balances should remain. Run `scripts/verify-persistence.ps1` first to verify this against your actual local MongoDB. This real-database check was not executed in the build workspace.

The public concept gallery and seed photographs are labelled illustrations. Do not present them as real client projects. The sample PDF is demonstration content; uploaded real quotation documents must match the structured amounts entered by Admin.
