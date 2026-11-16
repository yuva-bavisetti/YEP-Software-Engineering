"""The 42 specified acceptance scenarios, traced through one actual API journey.
Each parametrized assertion records an observed result. MongoDB restart cases are
explicitly skipped with mongomock; component/browser evidence is distinguished.
"""

import os, sys, uuid, subprocess, socket, time
from pathlib import Path
import pytest, bcrypt, mongomock, httpx
from pymongo import MongoClient
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main as m
from app.demo_assets import quotation_pdf, room_png

CASES = [
    "Customer logs in",
    "Customer submits request",
    "Admin receives request",
    "Manager cannot receive unassigned request",
    "Admin completes inspection",
    "Inspection required before quotation",
    "Admin uploads Phase 1 PDF",
    "Duration mandatory",
    "Customer views quotation",
    "Customer accepts Phase 1",
    "Admin creates project",
    "Admin creates milestones",
    "Admin assigns Manager",
    "Assigned Manager sees project",
    "Manager assigns Workers",
    "Workers see project and milestones",
    "Worker sees current phase and duration",
    "Worker uploads internal progress photo",
    "Photo initially Pending",
    "Unverified photo hidden from Customer",
    "Manager approves evidence",
    "Verified photo shared without new upload",
    "Customer views published progress",
    "Customer sends query image and text",
    "Admin and Manager respond",
    "Admin creates subsequent quotation",
    "Later phase belongs to same project",
    "Customer sees phase quotation history",
    "Admin records offline payment",
    "Customer payable paid balance correct",
    "Manager financial access denied",
    "Worker financial access denied",
    "Worker Customer Chat access denied",
    "Customer Internal Chat access denied",
    "Unassigned users cannot access project",
    "Chat survives backend restart with MongoDB",
    "Payment and quotation survive backend restart",
    "Four dashboard APIs load",
    "Public data and page routing available",
    "Five AI navigation and setup interfaces remain",
    "AI screens not replaced with placeholders",
    "No external AI integration introduced",
]


def restarted_records(database, uploads, cookies, pid):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {
        **os.environ,
        "MONGO_URL": os.environ["MONGO_TEST_URL"],
        "MONGO_DB": database,
        "UPLOAD_DIR": str(uploads),
    }

    def start():
        p = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(100):
            if p.poll() is not None:
                raise RuntimeError("Restart probe could not start backend")
            try:
                if (
                    httpx.get(
                        f"http://127.0.0.1:{port}/api/health", timeout=2
                    ).status_code
                    == 200
                ):
                    return p
            except httpx.TransportError:
                pass
            time.sleep(0.1)
        p.terminate()
        p.wait(timeout=10)
        raise RuntimeError("Restart probe timeout")

    proc = None
    try:
        proc = start()
        client = httpx.Client(
            base_url=f"http://127.0.0.1:{port}", cookies=dict(cookies), timeout=10
        )
        before = [
            client.get("/api" + path).json()
            for path in (
                f"/projects/{pid}/chat/customer",
                f"/projects/{pid}/finance",
                "/quotes",
            )
        ]
        proc.terminate()
        proc.wait(timeout=10)
        proc = start()
        after = [
            client.get("/api" + path).json()
            for path in (
                f"/projects/{pid}/chat/customer",
                f"/projects/{pid}/finance",
                "/quotes",
            )
        ]
        return before[0] == after[0], before[1:] == after[1:]
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)


@pytest.fixture(scope="module")
def observed(tmp_path_factory):
    root = tmp_path_factory.mktemp("acceptance")
    old_db, old_upload = m.db, m.UPLOAD
    engine = (
        MongoClient(os.environ["MONGO_TEST_URL"])
        if os.getenv("MONGO_TEST_URL")
        else mongomock.MongoClient()
    )
    name = "yep_test_acceptance_" + uuid.uuid4().hex
    m.db = engine[name]
    m.UPLOAD = root
    m.init_indexes()
    clients = {}
    users = {}
    results = {}
    password = bcrypt.hashpw(b"Demo@12345", bcrypt.gensalt()).decode()
    for email, role in [
        ("customer", "CUSTOMER"),
        ("owner", "ADMIN"),
        ("manager", "MANAGER"),
        ("worker", "WORKER"),
        ("other", "CUSTOMER"),
        ("unassigned", "MANAGER"),
        ("outsider", "WORKER"),
    ]:
        users[email] = m.insert(
            "users",
            {
                "name": email.title(),
                "email": email + "@yep.local",
                "role": role,
                "active": True,
                "password": password,
            },
        )
        c = TestClient(m.app)
        r = c.post(
            "/api/auth/login",
            json={"email": email + "@yep.local", "password": "Demo@12345"},
        )
        assert r.status_code == 200, r.text
        clients[email] = c
    for service in [
        "Interior painting",
        "Exterior painting",
        "Wall finishing",
        "False ceiling",
        "Flooring",
        "Tiling",
        "Waterproofing",
        "Renovation",
        "Repair and maintenance",
    ]:
        m.insert(
            "services",
            {
                "name": service,
                "description": "Professional service with preparation and quality inspection",
                "active": True,
            },
        )
    a, c, manager, w = [clients[k] for k in ("owner", "customer", "manager", "worker")]

    def post(client, path, data=None, status=200):
        r = client.post("/api" + path, json=data)
        assert r.status_code == status, (path, r.status_code, r.text)
        return r.json()

    def file(client, pdf=False):
        r = client.post(
            "/api/files",
            files={
                "file": (
                    "quotation.pdf" if pdf else "room.png",
                    quotation_pdf() if pdf else room_png(),
                    "application/pdf" if pdf else "image/png",
                )
            },
        )
        assert r.status_code == 200, r.text
        return r.json()["id"]

    try:
        results[1] = c.get("/api/auth/me").json()["role"] == "CUSTOMER"
        r = post(
            c,
            "/requests",
            {
                "service": "Interior painting",
                "property_type": "Apartment",
                "location": "Pune",
                "area": 1200,
                "description": "Paint the rooms and restore the surfaces",
                "preferred_date": "2026-12-01",
                "file_ids": [file(c)],
            },
        )
        rid = r["id"]
        results[2] = r["status"] == "Submitted"
        results[3] = any(x["id"] == rid for x in a.get("/api/requests").json())
        results[4] = manager.get("/api/requests").status_code == 403
        data = {
            "phase": 1,
            "title": "Preparation",
            "description": "Prepare and paint the selected rooms",
            "amount": "10000",
            "duration": 10,
            "pdf_id": file(a, True),
            "terms": "Materials and labour included",
        }
        results[6] = a.post(f"/api/requests/{rid}/quotes", json=data).status_code == 409
        post(
            a,
            f"/requests/{rid}/inspection",
            {
                "date": "2026-11-16",
                "measurements": "1200 sq ft",
                "notes": "Ready for preparation",
                "completed": True,
            },
        )
        results[5] = a.get(f"/api/requests/{rid}/inspection").json()["completed"]
        q = post(a, f"/requests/{rid}/quotes", data)
        results[7] = a.get("/api/files/" + q["pdf_id"]).content.startswith(b"%PDF")
        results[8] = (
            a.post(
                f"/api/requests/{rid}/quotes", json={**data, "duration": 0}
            ).status_code
            == 422
        )
        post(a, f"/quotes/{q['id']}/publish")
        results[9] = c.get("/api/files/" + q["pdf_id"]).status_code == 200
        post(c, f"/quotes/{q['id']}/decision", {"decision": "Accepted"})
        results[10] = c.get("/api/quotes").json()[0]["status"] == "Accepted"
        p = post(
            a,
            "/projects",
            {
                "quote_id": q["id"],
                "title": "Acceptance residence",
                "manager_id": users["manager"]["id"],
                "start_date": "2026-12-01",
                "deadline": "2026-12-20",
            },
        )
        pid = p["id"]
        results[11] = p["initial_quote_id"] == q["id"]
        ms = post(
            a,
            f"/projects/{pid}/milestones",
            {"title": "Prepare surfaces", "phase": 1, "deadline": "2026-12-10"},
        )
        results[12] = ms["progress"] == 0
        results[13] = p["manager_id"] == users["manager"]["id"]
        results[14] = manager.get("/api/projects").json()[0]["id"] == pid
        post(manager, f"/projects/{pid}/workers", {"worker_id": users["worker"]["id"]})
        results[15] = w.get("/api/projects").json()[0]["id"] == pid
        results[16] = (
            w.get(f"/api/projects/{pid}/milestones").json()[0]["id"] == ms["id"]
        )
        summary = w.get("/api/dashboard").json()
        results[17] = summary["current_phases"][0]["phase"]["duration"] == 10
        image = file(w)
        message = post(
            w,
            f"/projects/{pid}/chat/internal",
            {"text": "Prepared surfaces", "file_id": image},
        )
        results[18] = message["file_id"] == image
        results[19] = message["verification"] == "Pending"
        results[20] = (
            c.get("/api/files/" + image).status_code == 403
            and c.get(f"/api/projects/{pid}/chat/customer").json() == []
        )
        post(
            manager,
            f"/messages/{message['id']}/verify",
            {"approved": True, "share": False},
        )
        results[21] = (
            manager.get(f"/api/projects/{pid}/chat/internal").json()[0]["verification"]
            == "Approved"
        )
        count = m.db.files.count_documents({})
        post(
            manager,
            f"/messages/{message['id']}/share",
            {"text": "Verified preparation complete"},
        )
        results[22] = m.db.files.count_documents({}) == count
        results[23] = (
            c.get("/api/files/" + image).status_code == 200
            and c.get(f"/api/projects/{pid}/chat/customer").json()[0]["verification"]
            == "Approved"
        )
        query = post(
            c,
            f"/projects/{pid}/chat/customer",
            {"text": "Please review this corner", "file_id": file(c)},
        )
        results[24] = query["sender_id"] == users["customer"]["id"]
        replies = [
            post(
                staff,
                f"/projects/{pid}/chat/customer",
                {"text": "We will review the corner"},
            )
            for staff in (a, manager)
        ]
        results[25] = len(replies) == 2
        q2 = post(
            a,
            f"/requests/{rid}/quotes",
            {
                **data,
                "phase": 2,
                "title": "Finishing",
                "amount": "5000",
                "pdf_id": file(a, True),
            },
        )
        results[26] = q2["phase"] == 2
        post(a, f"/quotes/{q2['id']}/publish")
        results[27] = m.db.projects.count_documents({}) == 1 and q2["project_id"] == pid
        results[28] = len(c.get("/api/quotes").json()) == 2
        receipt = post(
            a,
            f"/projects/{pid}/payments",
            {
                "amount": "3000",
                "date": "2026-11-16",
                "method": "Cash",
                "verification": "Cash checked offline by Admin",
                "idempotency_key": "acceptance-payment-001",
            },
        )
        results[29] = receipt["verified_by"] == users["owner"]["id"]
        f = c.get(f"/api/projects/{pid}/finance").json()
        results[30] = (f["total_cents"], f["paid_cents"], f["balance_cents"]) == (
            1500000,
            300000,
            1200000,
        )
        for num, person in [(31, manager), (32, w)]:
            results[num] = (
                person.get(f"/api/projects/{pid}/finance").status_code == 403
                and person.get("/api/quotes").status_code == 403
                and person.get("/api/files/" + q["pdf_id"]).status_code == 403
            )
        results[33] = w.get(f"/api/projects/{pid}/chat/customer").status_code == 403
        results[34] = c.get(f"/api/projects/{pid}/chat/internal").status_code == 403
        results[35] = all(
            clients[key].get(f"/api/projects/{pid}/milestones").status_code == 403
            for key in ("other", "unassigned", "outsider")
        )
        results[36], results[37] = (
            restarted_records(name, root, c.cookies, pid)
            if os.getenv("MONGO_TEST_URL")
            else (None, None)
        )
        results[38] = all(
            clients[key].get("/api/dashboard").status_code == 200
            for key in ("customer", "owner", "manager", "worker")
        )
        results[39] = (
            len(c.get("/api/services").json()) == 9
            and c.get("/api/public/projects").status_code == 200
        )
        source = (
            Path(__file__).resolve().parents[2] / "frontend/src/features/Dashboard.tsx"
        ).read_text()
        ai = (
            Path(__file__).resolve().parents[2] / "frontend/src/features/AIStudio.tsx"
        ).read_text()
        results[40] = all(
            name in source
            for name in (
                "AI Design Studio",
                "AI Design Assistant",
                "AI Cost Estimator",
                "Smart Recommendations",
                "AI Project Insights",
            )
        )
        results[41] = (
            "coming soon" not in ai.lower() and "<input" in ai and "<textarea" in ai
        )
        results[42] = not any(
            key in ai
            for key in ("api.openai.com", "api.anthropic.com", "emergent", "sk-")
        )
        yield results
    finally:
        engine.drop_database(name)
        m.db, m.UPLOAD = old_db, old_upload
        engine.close()


@pytest.mark.parametrize(
    "number", range(1, 43), ids=[f"{i:02d}-{title}" for i, title in enumerate(CASES, 1)]
)
def test_acceptance(number, observed):
    if observed[number] is None:
        pytest.skip(
            "Real MongoDB and backend-process restart required; no durability claim from mongomock"
        )
    assert observed[number], CASES[number - 1]
