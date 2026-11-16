"""Workflow and permission integration tests. MONGO_TEST_URL opts into real MongoDB.
The default isolated mongomock database verifies API logic, not disk durability.
"""

import os, sys, base64
from pathlib import Path
import pytest, mongomock, bcrypt
from pymongo import MongoClient
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main as m

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII="
)
PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"


@pytest.fixture()
def env(tmp_path, monkeypatch):
    client = (
        MongoClient(os.environ["MONGO_TEST_URL"])
        if os.getenv("MONGO_TEST_URL")
        else mongomock.MongoClient()
    )
    name = "yep_test_" + m.secrets.token_hex(6)
    monkeypatch.setattr(m, "db", client[name])
    monkeypatch.setattr(m, "UPLOAD", tmp_path)
    m.init_indexes()
    m.insert(
        "services",
        {
            "name": "Interior painting",
            "description": "Professional painting service",
            "active": True,
        },
    )
    password = bcrypt.hashpw(b"Demo@12345", bcrypt.gensalt()).decode()
    users = {}
    clients = {}
    for role, email in [
        ("ADMIN", "owner"),
        ("CUSTOMER", "customer"),
        ("MANAGER", "manager"),
        ("WORKER", "worker"),
        ("CUSTOMER", "other"),
        ("MANAGER", "unassigned"),
        ("WORKER", "outsider"),
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
        result = c.post(
            "/api/auth/login",
            json={"email": email + "@yep.local", "password": "Demo@12345"},
        )
        assert result.status_code == 200, result.text
        assert "password" not in result.json()
        clients[email] = c
    yield clients, users
    client.drop_database(name)


def call(c, path, data=None, code=200, method="post"):
    r = (
        getattr(c, method)("/api" + path, json=data)
        if method != "get"
        else c.get("/api" + path)
    )
    assert r.status_code == code, (path, r.status_code, r.text)
    return r.json()


def upload(c, kind="pdf"):
    return c.post(
        "/api/files",
        files={
            "file": (
                "quote.pdf" if kind == "pdf" else "progress.png",
                PDF if kind == "pdf" else PNG,
                "application/pdf" if kind == "pdf" else "image/png",
            )
        },
    ).json()["id"]


def request(c):
    return call(
        c,
        "/requests",
        {
            "service": "Interior painting",
            "property_type": "House",
            "location": "Pune, Maharashtra",
            "area": 900,
            "rooms": 3,
            "description": "Repaint living room and bedrooms",
            "file_ids": [upload(c, "image")],
        },
    )


def inspection(c, rid):
    return call(
        c,
        f"/requests/{rid}/inspection",
        {
            "date": "2026-11-16",
            "measurements": "900 square feet",
            "notes": "Surface preparation needed",
            "completed": True,
        },
    )


def quote(c, rid, phase=1):
    return call(
        c,
        f"/requests/{rid}/quotes",
        {
            "phase": phase,
            "title": f"Phase {phase} work",
            "description": "Prepare and paint the selected spaces",
            "amount": "25000.50",
            "duration": 14,
            "pdf_id": upload(c),
            "terms": "Materials included; offline payment only",
        },
    )


def setup_project(env):
    cs, us = env
    a, c = cs["owner"], cs["customer"]
    r = request(c)
    inspection(a, r["id"])
    q = quote(a, r["id"])
    call(a, f"/quotes/{q['id']}/publish")
    call(c, f"/quotes/{q['id']}/decision", {"decision": "Accepted"})
    p = call(
        a,
        "/projects",
        {
            "quote_id": q["id"],
            "title": "Home renovation",
            "manager_id": us["manager"]["id"],
            "start_date": "2026-11-17",
            "deadline": "2026-12-01",
        },
    )
    return r, q, p


def test_complete_end_to_end(env):
    cs, us = env
    a, c, manager, w = [cs[x] for x in ("owner", "customer", "manager", "worker")]
    r = request(c)
    rid = r["id"]
    assert call(a, "/requests", method="get")[0]["id"] == rid
    call(manager, "/requests", code=403, method="get")
    call(
        manager,
        f"/requests/{rid}/inspection",
        {"date": "2026-11-16", "measurements": "900 sq ft", "notes": "Site reviewed"},
        403,
    )
    payload = {
        "phase": 1,
        "title": "Surface preparation",
        "description": "Prepare the walls before painting",
        "amount": "25000.50",
        "duration": 14,
        "pdf_id": upload(a),
        "terms": "Includes materials",
    }
    call(a, f"/requests/{rid}/quotes", payload, 409)
    inspection(a, rid)
    q = call(a, f"/requests/{rid}/quotes", payload)
    assert call(c, "/quotes", method="get") == []
    call(a, f"/quotes/{q['id']}/publish")
    call(manager, "/quotes", code=403, method="get")
    project_data = {
        "quote_id": q["id"],
        "title": "Apartment refresh",
        "manager_id": us["manager"]["id"],
        "start_date": "2026-11-17",
        "deadline": "2026-12-01",
    }
    call(a, "/projects", project_data, 409)
    call(c, f"/quotes/{q['id']}/decision", {"decision": "Accepted"})
    call(c, f"/quotes/{q['id']}/decision", {"decision": "Accepted"}, 409)
    p = call(a, "/projects", project_data)
    pid = p["id"]
    assert p["channels"] == ["internal", "customer"]
    call(a, "/projects", project_data, 409)
    assert call(manager, "/projects", method="get")[0]["id"] == pid
    assert call(w, "/projects", method="get") == []
    call(manager, f"/projects/{pid}/workers", {"worker_id": us["worker"]["id"]})
    call(manager, f"/projects/{pid}/workers", {"worker_id": us["worker"]["id"]})
    assert len(call(w, "/projects", method="get")[0]["worker_ids"]) == 1
    view = call(w, "/projects", method="get")[0]
    assert view["phases"][0]["duration"] == 14
    assert "initial_quote_id" not in view
    milestone = call(
        a,
        f"/projects/{pid}/milestones",
        {"title": "Wall preparation", "phase": 1, "deadline": "2026-11-25"},
    )
    call(w, f"/milestones/{milestone['id']}", {"progress": 100}, 403, method="patch")
    t = call(
        manager,
        f"/projects/{pid}/tasks",
        {
            "title": "Prepare walls",
            "worker_id": us["worker"]["id"],
            "deadline": "2026-11-25",
        },
    )
    call(w, f"/tasks/{t['id']}", {"decision": "Completed"}, method="patch")
    photo = upload(w, "image")
    msg = call(
        w,
        f"/projects/{pid}/chat/internal",
        {"text": "Wall preparation complete", "file_id": photo},
    )
    assert msg["verification"] == "Pending"
    assert call(c, f"/projects/{pid}/chat/customer", method="get") == []
    assert c.get("/api/files/" + photo).status_code == 403
    call(w, f"/messages/{msg['id']}/verify", {"approved": True, "share": True}, 403)
    call(
        manager,
        f"/messages/{msg['id']}/verify",
        {"approved": True, "share": True, "text": "Verified wall preparation"},
    )
    assert c.get("/api/files/" + photo).status_code == 200
    shared = call(c, f"/projects/{pid}/chat/customer", method="get")
    assert shared[0]["source_id"] == msg["id"]
    assert shared[0]["verification"] == "Approved"
    call(
        manager, f"/messages/{msg['id']}/verify", {"approved": True, "share": True}, 409
    )
    call(
        c,
        f"/projects/{pid}/chat/customer",
        {"text": "Can we check this corner?", "file_id": upload(c, "image")},
    )
    call(
        a,
        f"/projects/{pid}/chat/customer",
        {"text": "We will review this at the next visit."},
    )
    call(
        manager,
        f"/projects/{pid}/chat/customer",
        {"text": "I have shared instructions with the team."},
    )
    q2 = quote(a, rid, 2)
    call(a, f"/quotes/{q2['id']}/publish")
    assert len(call(c, "/quotes", method="get")) == 2
    pay = {
        "amount": "10000.25",
        "date": "2026-11-18",
        "method": "UPI",
        "reference": "DEMO001",
        "verification": "Confirmed against offline bank statement",
        "idempotency_key": "payment-demo-0001",
    }
    payment = call(a, f"/projects/{pid}/payments", pay)
    call(a, f"/projects/{pid}/payments", pay, 409)
    f = call(c, f"/projects/{pid}/finance", method="get")
    assert f["total_cents"] == 5000100
    assert f["paid_cents"] == 1000025
    assert f["balance_cents"] == 4000075
    for role in ("manager", "worker"):
        call(cs[role], f"/projects/{pid}/finance", code=403, method="get")
        assert cs[role].get("/api/files/" + q["pdf_id"]).status_code == 403
    call(w, f"/projects/{pid}/chat/customer", code=403, method="get")
    call(c, f"/projects/{pid}/chat/internal", code=403, method="get")
    for role in ("other", "unassigned", "outsider"):
        for path in ("milestones", "tasks", "chat/internal", "chat/customer"):
            call(cs[role], f"/projects/{pid}/{path}", code=403, method="get")
    call(
        a,
        f"/payments/{payment['id']}/reverse",
        {"text": "Correction: wrong project selected"},
    )
    call(a, f"/payments/{payment['id']}/reverse", {"text": "Correction repeated"}, 409)
    assert call(c, f"/projects/{pid}/finance", method="get")["paid_cents"] == 0
    call(manager, f"/milestones/{milestone['id']}", {"progress": 100}, method="patch")
    for ph in (1, 2):
        call(
            a,
            f"/projects/{pid}/phases/{ph}",
            {
                "title": f"Phase {ph}",
                "start_date": "2026-11-17",
                "deadline": "2026-12-01",
                "status": "Completed",
            },
            method="patch",
        )
    call(manager, f"/projects/{pid}/complete", code=409)
    call(
        manager,
        f"/projects/{pid}/quality",
        {"title": "Final surface and finish inspection", "passed": True},
    )
    call(manager, f"/projects/{pid}/complete")
    call(
        c,
        f"/projects/{pid}/feedback",
        {"rating": 5, "text": "Very happy with the completed work"},
    )
    # A new HTTP client retains session and reads the same database records.
    fresh = TestClient(m.app)
    fresh.cookies.update(c.cookies)
    assert len(fresh.get(f"/api/projects/{pid}/chat/customer").json()) == 4


def test_validation_and_authentication(env):
    cs, us = env
    c = cs["customer"]
    anon = TestClient(m.app)
    assert anon.get("/api/projects").status_code == 401
    assert (
        anon.post(
            "/api/auth/login",
            json={"email": "owner@yep.local", "password": "incorrect"},
        ).status_code
        == 401
    )
    assert (
        anon.post(
            "/api/auth/register",
            json={"name": "New", "email": "new@example.com", "password": "short"},
        ).status_code
        == 422
    )
    assert (
        anon.post(
            "/api/auth/register",
            json={
                "name": "New",
                "email": "new@example.com",
                "password": "Valid@12345",
                "role": "ADMIN",
            },
        ).status_code
        == 422
    )
    assert c.post("/api/requests", json={"service": "x"}).status_code == 422
    assert (
        c.post(
            "/api/files",
            files={"file": ("evil.html", b"<script>alert(1)</script>", "text/html")},
        ).status_code
        == 422
    )
    assert (
        c.post(
            "/api/requests", json={}, headers={"origin": "https://evil.example"}
        ).status_code
        == 403
    )
    call(c, "/auth/logout")
    assert c.get("/api/auth/me").status_code == 401


def test_revision_history_and_private_pdf(env):
    cs, us = env
    a, c = cs["owner"], cs["customer"]
    r = request(c)
    inspection(a, r["id"])
    q = quote(a, r["id"])
    assert c.get("/api/files/" + q["pdf_id"]).status_code == 403
    call(a, f"/quotes/{q['id']}/publish")
    call(c, f"/quotes/{q['id']}/decision", {"decision": "Revision Requested"})
    q2 = quote(a, r["id"])
    assert q2["revision"] == 2
    assert m.db.quotes.count_documents({"request_id": r["id"]}) == 2
    call(a, f"/quotes/{q2['id']}/publish")
    call(c, f"/quotes/{q2['id']}/decision", {"decision": "Accepted"})
    assert cs["other"].get("/api/files/" + q2["pdf_id"]).status_code == 403


def test_inactive_accounts_and_role_boundaries(env):
    cs, us = env
    r, q, p = setup_project(env)
    a = cs["owner"]
    pid = p["id"]
    assert cs["manager"].post("/api/projects", json={}).status_code == 422
    call(
        a,
        f"/users/{us['manager']['id']}/active",
        {"decision": "inactive"},
        method="patch",
    )
    assert cs["manager"].get("/api/projects").status_code == 403
    assert (
        cs["manager"]
        .post(
            "/api/auth/login",
            json={"email": "manager@yep.local", "password": "Demo@12345"},
        )
        .status_code
        == 401
    )


def test_boq_calculations_draft_edit_and_role_permissions(env):
    cs, us = env
    a, c, manager, w = [cs[x] for x in ("owner", "customer", "manager", "worker")]
    r = request(c)
    inspection(a, r["id"])
    payload = {
        "phase": 1,
        "title": "Detailed BOQ",
        "description": "Painting and preparation of walls",
        "amount": "250.75",
        "duration": 4,
        "pdf_id": upload(a),
        "terms": "Includes listed materials only",
        "items": [
            {
                "description": "Wall finish",
                "category": "Material",
                "quantity": "2.5",
                "unit": "litres",
                "unit_price": "99.00",
            }
        ],
        "tax_percent": "10",
        "discount": "21.50",
    }
    # 2.5 * 99 = 247.50; 10% = 24.75; less 21.50 = 250.75.
    q = call(a, f"/requests/{r['id']}/quotes", payload)
    assert q["amount_cents"] == 25075
    assert q["items"][0]["total_cents"] == 24750
    for role in (manager, w, c):
        call(role, f"/requests/{r['id']}/quotes", payload, 403)
    bad = {**payload, "amount": "1.00"}
    call(a, f"/quotes/{q['id']}", bad, 422, method="put")
    edited = call(a, f"/quotes/{q['id']}", {**payload, "duration": 5}, method="put")
    assert edited["duration"] == 5
    call(a, f"/quotes/{q['id']}/publish")
    call(a, f"/quotes/{q['id']}", payload, 409, method="put")
    assert c.get("/api/files/" + q["pdf_id"]).status_code == 200
    assert cs["other"].get("/api/files/" + q["pdf_id"]).status_code == 403


def test_request_additional_info_and_private_attachments(env):
    cs, us = env
    a, c = cs["owner"], cs["customer"]
    r = request(c)
    call(
        a,
        f"/requests/{r['id']}/status",
        {
            "status": "More Information Required",
            "note": "Please confirm the room dimensions",
        },
        method="patch",
    )
    file = upload(c, "image")
    call(
        cs["other"],
        f"/requests/{r['id']}/reply",
        {"text": "Unrelated reply", "file_ids": []},
        403,
    )
    call(
        c,
        f"/requests/{r['id']}/reply",
        {"text": "The room is 15 by 12 feet", "file_ids": [file]},
    )
    refreshed = call(c, "/requests", method="get")[0]
    assert refreshed["status"] == "Under Review"
    assert len(refreshed["file_ids"]) == 2
    assert cs["manager"].get("/api/files/" + file).status_code == 403
    call(
        c,
        f"/requests/{r['id']}/reply",
        {"text": "Duplicate reply", "file_ids": []},
        409,
    )


def test_invalid_payments_duration_and_foreign_files(env):
    cs, us = env
    r, q, p = setup_project(env)
    a, c = cs["owner"], cs["customer"]
    pid = p["id"]
    call(
        a,
        f"/projects/{pid}/payments",
        {
            "amount": "-1",
            "date": "2026-11-16",
            "method": "Cash",
            "verification": "Offline verified",
            "idempotency_key": "invalid-test-01",
        },
        422,
    )
    for role in ("customer", "manager", "worker"):
        call(
            cs[role],
            f"/projects/{pid}/payments",
            {
                "amount": "1",
                "date": "2026-11-16",
                "method": "Cash",
                "verification": "Offline verified",
                "idempotency_key": "invalid-test-01",
            },
            403,
        )
    foreign = upload(cs["other"], "image")
    call(
        c,
        f"/projects/{pid}/chat/customer",
        {"text": "Must not claim foreign file", "file_id": foreign},
        403,
    )
    payload = {
        "phase": 2,
        "title": "Later phase",
        "description": "Final finishes",
        "amount": "100",
        "duration": 0,
        "pdf_id": upload(a),
        "terms": "Offline only",
    }
    call(a, f"/requests/{r['id']}/quotes", payload, 422)


def test_demo_seed_is_repeatable_and_non_destructive(tmp_path, monkeypatch):
    from seed import seed

    db = mongomock.MongoClient()["seed_test"]
    monkeypatch.setattr(m, "db", db)
    monkeypatch.setattr(m, "UPLOAD", tmp_path)
    seed()
    counts = {c: db[c].count_documents({}) for c in db.list_collection_names()}
    db.projects.update_one({}, {"$set": {"title": "User edited project"}})
    seed()
    assert counts == {c: db[c].count_documents({}) for c in db.list_collection_names()}
    assert db.projects.find_one()["title"] == "User edited project"
    assert db.quotes.count_documents({}) == 2
    assert db.payments.count_documents({}) == 1


def test_task_reassignment_and_milestone_deadlines(env):
    cs, us = env
    r, q, p = setup_project(env)
    a, manager, w = cs["owner"], cs["manager"], cs["worker"]
    pid = p["id"]
    for key in ("worker", "outsider"):
        call(manager, f"/projects/{pid}/workers", {"worker_id": us[key]["id"]})
    payload = {
        "title": "Prepare the surface",
        "worker_id": us["worker"]["id"],
        "deadline": "2026-11-24",
        "description": "Use the specified primer",
        "priority": "Normal",
    }
    t = call(manager, f"/projects/{pid}/tasks", payload)
    assert len(call(w, f"/projects/{pid}/tasks", method="get")) == 1
    call(
        manager,
        f"/tasks/{t['id']}",
        {**payload, "worker_id": us["outsider"]["id"]},
        method="put",
    )
    assert call(w, f"/projects/{pid}/tasks", method="get") == []
    call(w, f"/tasks/{t['id']}", {"decision": "Completed"}, 403, method="patch")
    call(cs["outsider"], f"/tasks/{t['id']}", {"decision": "Completed"}, method="patch")
    milestone = call(
        a,
        f"/projects/{pid}/milestones",
        {"title": "Preparation", "phase": 1, "deadline": "2026-11-24"},
    )
    edit = {"title": "Preparation review", "phase": 1, "deadline": "2026-11-25"}
    call(w, f"/milestones/{milestone['id']}", edit, 403, method="put")
    call(manager, f"/milestones/{milestone['id']}", edit, method="put")
    assert (
        call(w, f"/projects/{pid}/milestones", method="get")[0]["deadline"]
        == "2026-11-25"
    )
