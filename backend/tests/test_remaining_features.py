"""Regression coverage for audit findings. All fixtures use isolated databases."""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from pymongo.errors import ServerSelectionTimeoutError
import pytest
from test_workflow import (
    env,
    call,
    setup_project,
    upload,
    quote,
    request,
    inspection,
    m,
)


def test_registration_profile_and_session_revocation(env):
    cs, us = env
    c = TestClient(m.app)
    body = {
        "name": "New Customer",
        "email": "new@yep.local",
        "password": "Demo@12345",
        "phone": "1234567890",
    }
    result = call(c, "/auth/register", body)
    assert result["role"] == "CUSTOMER" and "password" not in result
    call(c, "/auth/register", body, 409)
    call(c, "/auth/login", {"email": body["email"], "password": body["password"]})
    data = call(
        c,
        "/profile",
        {
            "name": "Updated Customer",
            "email": "updated@yep.local",
            "phone": "98765",
            "address": "Pune",
            "password": "Changed@12345",
        },
        method="patch",
    )
    assert data["email"] == "updated@yep.local" and data["address"] == "Pune"
    call(
        TestClient(m.app),
        "/auth/login",
        {"email": body["email"], "password": body["password"]},
        401,
    )
    call(
        TestClient(m.app),
        "/auth/login",
        {"email": "updated@yep.local", "password": "Changed@12345"},
    )
    call(
        c,
        "/profile",
        {"name": "No duplicate", "email": "owner@yep.local"},
        409,
        method="patch",
    )
    call(c, "/auth/logout")
    assert c.get("/api/auth/me").status_code == 401


def test_employee_crud_roles_and_directory_privacy(env):
    cs, us = env
    a, manager = cs["owner"], cs["manager"]
    body = {
        "name": "New Painter",
        "email": "painter@yep.local",
        "password": "Demo@12345",
        "role": "WORKER",
    }
    employee = call(a, "/users", body)
    call(manager, "/users", body, 403)
    call(a, "/users", {**body, "email": "bad@yep.local", "role": "ADMIN"}, 422)
    edited = call(
        a,
        "/users/" + employee["id"],
        {"name": "Painter Updated", "email": "painter@yep.local", "phone": "12345"},
        method="patch",
    )
    assert edited["role"] == "WORKER"  # omitted role must not become null
    changed = call(
        a,
        "/users/" + employee["id"],
        {"name": "New Manager", "email": "painter@yep.local", "role": "MANAGER"},
        method="patch",
    )
    assert changed["role"] == "MANAGER"
    call(
        a,
        "/users/" + employee["id"] + "/active",
        {"decision": "inactive"},
        method="patch",
    )
    call(
        TestClient(m.app),
        "/auth/login",
        {"email": "painter@yep.local", "password": "Demo@12345"},
        401,
    )
    directory = call(manager, "/users", method="get")
    assert all("email" not in u and "password" not in u for u in directory)
    r, q, p = setup_project(env)
    call(
        a,
        "/users/" + us["manager"]["id"],
        {"name": "Role change blocked", "email": "manager@yep.local", "role": "WORKER"},
        409,
        method="patch",
    )


def test_services_images_enquiries_settings_and_history(env):
    cs, us = env
    a, c = cs["owner"], cs["customer"]
    anon = TestClient(m.app)
    image = upload(a, "image")
    service = call(
        a,
        "/services",
        {
            "name": "Restoration",
            "description": "Restoration with careful material selection",
            "image_id": image,
        },
    )
    assert (
        anon.get("/api/public/services/" + service["id"] + "/image").status_code == 200
    )
    call(
        a,
        "/services/" + service["id"],
        {
            "name": "Restoration",
            "description": "Updated restoration service description",
            "active": False,
            "image_id": image,
        },
        method="put",
    )
    assert (
        anon.get("/api/public/services/" + service["id"] + "/image").status_code == 404
    )
    assert not any(s["id"] == service["id"] for s in anon.get("/api/services").json())
    call(
        c,
        "/services",
        {"name": "Invalid", "description": "Customers must not add services"},
        403,
    )
    call(
        anon,
        "/enquiries",
        {
            "name": "Visitor",
            "email": "visitor@example.com",
            "message": "Please contact me about renovation",
            "phone": "12345",
        },
    )
    assert len(call(a, "/admin/enquiries", method="get")) == 1
    call(c, "/admin/enquiries", code=403, method="get")
    settings = {
        "business_name": "YEP",
        "email": "contact@yep.local",
        "phone": "12345",
        "location": "Pune service area",
    }
    call(a, "/admin/settings", settings, method="put")
    assert anon.get("/api/settings/public").json() == settings
    call(cs["manager"], "/admin/settings", settings, 403, method="put")
    r = request(c)
    history = call(
        a, "/admin/customers/" + us["customer"]["id"] + "/history", method="get"
    )
    assert history["requests"][0]["id"] == r["id"]
    assert "password" not in history["customer"]
    call(
        c,
        "/admin/customers/" + us["customer"]["id"] + "/history",
        code=403,
        method="get",
    )


def test_scheduled_inspection_keeps_photos_and_lifecycle_history(env):
    cs, us = env
    a, c = cs["owner"], cs["customer"]
    r = request(c)
    rid = r["id"]
    photo = upload(a, "image")
    payload = {
        "date": "2026-11-16",
        "measurements": "1200 sq ft",
        "notes": "Scheduled site inspection",
        "file_ids": [photo],
    }
    call(a, f"/requests/{rid}/inspection", payload)
    call(
        a,
        f"/requests/{rid}/inspection",
        {**payload, "date": "2026-11-17", "file_ids": [], "completed": True},
    )
    assert call(c, f"/requests/{rid}/inspection", method="get")["file_ids"] == [photo]
    call(a, f"/requests/{rid}/inspection", payload, 409)
    states = [h["status"] for h in call(c, "/requests", method="get")[0]["history"]]
    assert (
        "Submitted" in states
        and "Inspection Scheduled" in states
        and "Inspection Completed" in states
    )


def test_phase_planning_transitions_and_task_execution(env):
    cs, us = env
    r, q, p = setup_project(env)
    a, manager = cs["owner"], cs["manager"]
    pid = p["id"]
    payload = {"number": 101, "title": "Future phase", "duration": 7}
    call(a, f"/projects/{pid}/phases", payload)
    call(a, f"/projects/{pid}/phases", payload, 409)
    call(manager, f"/projects/{pid}/phases", {**payload, "number": 102}, 403)
    phase = {
        "title": "Future phase",
        "start_date": "2026-12-01",
        "deadline": "2026-12-07",
        "status": "Active",
    }
    call(
        a, f"/projects/{pid}/phases/101", phase, 409, method="patch"
    )  # no published quotation
    call(
        a,
        f"/projects/{pid}/phases/101",
        {**phase, "status": "Completed"},
        409,
        method="patch",
    )
    q2 = quote(a, r["id"], 101)
    call(a, f"/quotes/{q2['id']}/publish")
    call(
        a, f"/projects/{pid}/phases/101", phase, 409, method="patch"
    )  # preceding phase active
    phase_milestone = call(
        a,
        f"/projects/{pid}/milestones",
        {"title": "Initial verification", "phase": 1, "deadline": "2026-12-01"},
    )
    call(a, f"/milestones/{phase_milestone['id']}", {"progress": 100}, method="patch")
    initial = {
        "title": q["title"],
        "start_date": "2026-11-17",
        "deadline": "2026-12-01",
        "status": "Completed",
    }
    call(a, f"/projects/{pid}/phases/1", initial, method="patch")
    call(a, f"/projects/{pid}/phases/101", phase, method="patch")
    current = call(manager, "/dashboard", method="get")["current_phases"][0]["phase"]
    assert current["number"] == 101 and current["duration"] == 14
    call(
        a,
        f"/projects/{pid}/phases/1",
        {**initial, "status": "Active"},
        409,
        method="patch",
    )


def test_revision_accounting_overpayment_and_reversal(env):
    cs, us = env
    r, q, p = setup_project(env)
    a, c = cs["owner"], cs["customer"]
    pid = p["id"]
    q2 = quote(a, r["id"], 2)
    call(a, f"/quotes/{q2['id']}/publish")
    call(c, f"/quotes/{q2['id']}/decision", {"decision": "Revision Requested"})
    assert call(c, f"/projects/{pid}/finance", method="get")["total_cents"] == 2500050
    q3 = quote(a, r["id"], 2)
    assert q3["revision"] == 2
    call(a, f"/quotes/{q3['id']}/publish")
    assert call(c, f"/projects/{pid}/finance", method="get")["total_cents"] == 5000100
    payment = {
        "amount": "60000.00",
        "date": "2026-11-16",
        "method": "Bank Transfer",
        "verification": "Verified against offline statement",
        "idempotency_key": "overpayment-case-001",
    }
    receipt = call(a, f"/projects/{pid}/payments", payment)
    call(a, f"/projects/{pid}/payments", payment, 409)
    assert call(c, f"/projects/{pid}/finance", method="get")["balance_cents"] == -999900
    call(
        a,
        f"/payments/{receipt['id']}/reverse",
        {"text": "Correction for duplicated bank credit"},
    )
    assert call(c, f"/projects/{pid}/finance", method="get")["balance_cents"] == 5000100
    assert (
        m.db.payments.count_documents({}) == 2 and m.db.quotes.count_documents({}) == 3
    )


def test_material_quality_reports_and_stats(env):
    cs, us = env
    r, q, p = setup_project(env)
    a, manager = cs["owner"], cs["manager"]
    pid = p["id"]
    material = call(
        manager,
        f"/projects/{pid}/materials",
        {"name": "Primer", "quantity": 10, "unit": "litres", "status": "Shortage"},
    )
    assert (
        call(manager, "/reports", method="get")["shortages"][0]["id"] == material["id"]
    )
    call(
        manager,
        "/materials/" + material["id"],
        {"name": "Primer", "quantity": 10, "unit": "litres", "status": "Available"},
        method="put",
    )
    assert call(manager, "/reports", method="get")["shortages"] == []
    bad = {
        "title": "Final quality",
        "passed": True,
        "items": [{"label": "Clean finish", "passed": False}],
    }
    call(manager, f"/projects/{pid}/quality", bad, 422)
    call(
        manager,
        f"/projects/{pid}/quality",
        {"title": "Defect report", "passed": False},
        422,
    )
    call(
        manager,
        f"/projects/{pid}/quality",
        {
            **bad,
            "passed": False,
            "defects": "Uneven coat",
            "corrective_action": "Apply another coat",
        },
    )
    summary = call(a, "/admin/summary", method="get")
    assert (
        summary["customers"] == 2
        and summary["requests"] == 1
        and "project_months" in summary
    )
    report = call(manager, "/reports", method="get")
    assert len(report["projects"]) == 1
    assert all(
        key not in str(report)
        for key in ("amount_cents", "pdf_id", "password", "verified_receipts_cents")
    )
    assert call(cs["unassigned"], "/reports", method="get")["projects"] == []
    call(cs["worker"], "/reports", code=403, method="get")


def test_write_lease_and_recoverable_derived_views(env):
    cs, us = env
    r, q, p = setup_project(env)
    a, c = cs["owner"], cs["customer"]
    pid = p["id"]
    m.db.workflow_locks.insert_one(
        {
            "_id": "business",
            "owner": "other-process",
            "expires": datetime.now(timezone.utc) + timedelta(seconds=30),
        }
    )
    payload = {
        "amount": "1.00",
        "date": "2026-11-16",
        "method": "Cash",
        "verification": "Verified offline",
        "idempotency_key": "lease-retry-001",
    }
    call(a, f"/projects/{pid}/payments", payload, 409)
    m.db.workflow_locks.update_one(
        {"_id": "business"},
        {"$set": {"expires": datetime.now(timezone.utc) - timedelta(seconds=1)}},
    )
    call(a, f"/projects/{pid}/payments", payload)
    q2 = quote(a, r["id"], 2)
    call(a, f"/quotes/{q2['id']}/publish")
    m.db.projects.update_one(
        {"id": pid}, {"$pull": {"phases": {"number": 2}}, "$set": {"progress": 100}}
    )
    m.db.quotes.update_one({"id": q2["id"]}, {"$set": {"project_id": None}})
    m.db.requests.update_one({"id": r["id"]}, {"$set": {"status": "Submitted"}})
    result = call(c, "/projects", method="get")[0]
    assert len(result["phases"]) == 2 and result["progress"] == 0
    assert m.db.quotes.find_one({"id": q2["id"]})["project_id"] == pid
    assert call(c, "/requests", method="get")[0]["status"] == "Converted to Project"
    count = len(m.db.requests.find_one({"id": r["id"]})["history"])
    call(c, "/projects", method="get")
    assert len(m.db.requests.find_one({"id": r["id"]})["history"]) == count


def test_file_structure_size_ownership_and_missing_ids(env):
    cs, us = env
    a, c = cs["owner"], cs["customer"]
    for name, content, mime in [
        ("broken.pdf", b"%PDF-1.7\nnot a PDF", "application/pdf"),
        ("broken.png", b"\x89PNG\r\n\x1a\nnot an image", "image/png"),
        ("large.jpg", b"x" * (10 * 1024 * 1024 + 1), "image/jpeg"),
    ]:
        assert (
            a.post("/api/files", files={"file": (name, content, mime)}).status_code
            == 422
        )
    image = upload(a, "image")
    assert c.get("/api/files/" + image).status_code == 403
    assert c.get("/api/files/nonexistent-id").status_code == 404


def test_cross_project_isolation_and_completed_write_guard(env):
    cs, us = env
    r, q, p = setup_project(env)
    a = cs["owner"]
    pid = p["id"]
    other_request = request(cs["other"])
    inspection(a, other_request["id"])
    oq = quote(a, other_request["id"])
    call(a, f"/quotes/{oq['id']}/publish")
    call(cs["other"], f"/quotes/{oq['id']}/decision", {"decision": "Accepted"})
    other = call(
        a,
        "/projects",
        {
            "quote_id": oq["id"],
            "title": "Other customer project",
            "manager_id": us["unassigned"]["id"],
            "start_date": "2026-11-17",
            "deadline": "2026-12-01",
        },
    )
    for key in ("customer", "manager", "worker"):
        for suffix in (
            "milestones",
            "tasks",
            "chat/internal",
            "chat/customer",
            "quality",
        ):
            call(cs[key], f"/projects/{other['id']}/{suffix}", code=403, method="get")
    call(a, f"/projects/{pid}/workers", {"worker_id": us["worker"]["id"]})
    task = call(
        a,
        f"/projects/{pid}/tasks",
        {
            "title": "Assigned work",
            "worker_id": us["worker"]["id"],
            "deadline": "2026-11-20",
        },
    )
    m.db.projects.update_one({"id": pid}, {"$set": {"status": "Completed"}})
    call(
        cs["worker"],
        f"/tasks/{task['id']}",
        {"decision": "Completed"},
        409,
        method="patch",
    )


def test_completion_does_not_trust_rounded_cached_progress(env):
    cs, us = env
    r, q, p = setup_project(env)
    a = cs["owner"]
    pid = p["id"]
    ms = call(
        a,
        f"/projects/{pid}/milestones",
        {"title": "Finish all surfaces", "phase": 1, "deadline": "2026-12-01"},
    )
    call(a, f"/milestones/{ms['id']}", {"progress": 99}, method="patch")
    assert call(a, "/projects", method="get")[0]["progress"] == 99
    m.db.projects.update_one(
        {"id": pid}, {"$set": {"progress": 100, "phases.0.status": "Completed"}}
    )
    call(a, f"/projects/{pid}/quality", {"title": "Visual inspection", "passed": True})
    call(a, f"/projects/{pid}/complete", code=409)


def test_public_portfolio_publishes_only_verified_completed_work(env):
    cs, us = env
    r, q, p = setup_project(env)
    a, c, w = cs["owner"], cs["customer"], cs["worker"]
    pid = p["id"]
    anon = TestClient(m.app)
    call(a, f"/projects/{pid}/workers", {"worker_id": us["worker"]["id"]})
    image = upload(w, "image")
    msg = call(
        w,
        f"/projects/{pid}/chat/internal",
        {"text": "Finished surface", "file_id": image},
    )
    payload = {
        "title": "Completed renovation",
        "description": "A warm interior finish, published by the project team",
        "category": "Interior painting",
        "file_ids": [image],
        "published": True,
        "show_feedback": True,
    }
    call(a, f"/projects/{pid}/portfolio", payload, 409, method="put")
    ms = call(
        a,
        f"/projects/{pid}/milestones",
        {"title": "Complete finishes", "phase": 1, "deadline": "2026-12-01"},
    )
    call(
        a, f"/milestones/{ms['id']}", {"progress": 100, "publish": True}, method="patch"
    )
    call(
        a,
        f"/projects/{pid}/quality",
        {
            "title": "Final inspection",
            "passed": True,
            "items": [{"label": "Finish quality", "passed": True}],
        },
    )
    call(
        a,
        f"/projects/{pid}/phases/1",
        {
            "title": q["title"],
            "start_date": "2026-11-17",
            "deadline": "2026-12-01",
            "status": "Completed",
        },
        method="patch",
    )
    call(a, f"/projects/{pid}/complete")
    call(
        a, f"/projects/{pid}/portfolio", payload, 422, method="put"
    )  # evidence still Pending
    # A finished project is read-only for execution; approve before completion in real flow.
    m.db.projects.update_one({"id": pid}, {"$set": {"status": "Active"}})
    call(a, f"/messages/{msg['id']}/verify", {"approved": True, "share": True})
    m.db.projects.update_one({"id": pid}, {"$set": {"status": "Completed"}})
    call(
        c,
        f"/projects/{pid}/feedback",
        {"rating": 5, "text": "A careful and considered finish"},
    )
    call(a, f"/projects/{pid}/portfolio", payload, method="put")
    public = anon.get("/api/public/projects").json()
    assert len(public) == 1 and public[0]["feedback"]["rating"] == 5
    assert all(
        key not in public[0]
        for key in (
            "customer_id",
            "location",
            "manager_id",
            "amount_cents",
            "request_id",
        )
    )
    assert anon.get(f"/api/public/projects/{pid}/photos/{image}").status_code == 200
    assert anon.get("/api/public/projects?category=Flooring").json() == []
    call(a, f"/projects/{pid}/portfolio", {**payload, "published": False}, method="put")
    assert (
        anon.get("/api/public/projects").json() == []
        and anon.get(f"/api/public/projects/{pid}/photos/{image}").status_code == 404
    )


def test_project_hold_notifications_and_milestone_publication(env):
    cs, us = env
    r, q, p = setup_project(env)
    a, c, manager = cs["owner"], cs["customer"], cs["manager"]
    pid = p["id"]
    call(
        a,
        f"/projects/{pid}/status",
        {"status": "On Hold", "note": "Customer requested a pause"},
        method="patch",
    )
    call(
        manager,
        f"/projects/{pid}/milestones",
        {"title": "Should be paused", "phase": 1, "deadline": "2026-12-01"},
        409,
    )
    call(
        a,
        f"/projects/{pid}/status",
        {"status": "Active", "note": "Customer approved resuming work"},
        method="patch",
    )
    ms = call(
        manager,
        f"/projects/{pid}/milestones",
        {"title": "Verified milestone", "phase": 1, "deadline": "2026-12-01"},
    )
    call(
        manager,
        f"/milestones/{ms['id']}",
        {"progress": 50, "publish": True},
        method="patch",
    )
    messages = call(c, f"/projects/{pid}/chat/customer", method="get")
    assert any(x.get("milestone_id") == ms["id"] for x in messages)
    note = call(c, "/notifications", method="get")[0]
    call(c, "/notifications/" + note["id"] + "/read", method="patch")
    assert next(
        x for x in call(c, "/notifications", method="get") if x["id"] == note["id"]
    )["read"]
    call(
        cs["other"], "/notifications/" + note["id"] + "/read", code=404, method="patch"
    )


def test_mongo_api_error_response_is_actionable(env, monkeypatch):
    def unavailable(*args, **kwargs):
        raise ServerSelectionTimeoutError("test database is unavailable")

    monkeypatch.setattr(m.db, "command", unavailable)
    response = TestClient(m.app).get("/api/health")
    assert response.status_code == 503 and "MongoDB" in response.json()["detail"]


def test_concurrent_receipts_are_serialized_without_duplicate_ledger_entries(env):
    cs, us = env
    r, q, p = setup_project(env)
    a = cs["owner"]
    pid = p["id"]
    data = {
        "amount": "100.00",
        "date": "2026-11-16",
        "method": "Cash",
        "verification": "Confirmed offline receipt",
        "idempotency_key": "concurrent-receipt-001",
    }

    def submit(_):
        client = TestClient(m.app)
        client.cookies.update(a.cookies)
        return client.post(f"/api/projects/{pid}/payments", json=data).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(submit, range(2)))
    assert sorted(statuses) == [200, 409]
    assert m.db.payments.count_documents({"project_id": pid}) == 1
    assert (
        call(cs["customer"], f"/projects/{pid}/finance", method="get")["paid_cents"]
        == 10000
    )


def test_phase_execution_and_review_state_invariants(env):
    cs, us = env
    a, c, w = cs["owner"], cs["customer"], cs["worker"]
    r = request(c)
    inspection(a, r["id"])
    call(
        a,
        f"/requests/{r['id']}/status",
        {
            "status": "More Information Required",
            "note": "Please confirm the measurements",
        },
        method="patch",
    )
    assert (
        call(c, "/requests", method="get")[0]["status"] == "More Information Required"
    )
    payload = {
        "phase": 1,
        "title": "Initial work",
        "description": "Surface preparation",
        "amount": "1000",
        "duration": 7,
        "pdf_id": upload(a),
        "terms": "Includes preparation",
    }
    call(a, f"/requests/{r['id']}/quotes", payload, 409)
    call(
        c,
        f"/requests/{r['id']}/reply",
        {"text": "Confirmed the measurements are correct"},
    )
    q = call(a, f"/requests/{r['id']}/quotes", payload)
    call(a, f"/quotes/{q['id']}/publish")
    call(c, f"/quotes/{q['id']}/decision", {"decision": "Accepted"})
    p = call(
        a,
        "/projects",
        {
            "quote_id": q["id"],
            "title": "Phase invariants",
            "manager_id": us["manager"]["id"],
            "start_date": "2026-11-17",
            "deadline": "2026-12-01",
        },
    )
    pid = p["id"]
    call(a, f"/projects/{pid}/workers", {"worker_id": us["worker"]["id"]})
    call(
        a,
        f"/projects/{pid}/phases",
        {"number": 2, "title": "Planned finishes", "duration": 7},
    )
    task = call(
        a,
        f"/projects/{pid}/tasks",
        {
            "title": "Future finish",
            "phase": 2,
            "worker_id": us["worker"]["id"],
            "deadline": "2026-12-01",
        },
    )
    call(w, f"/tasks/{task['id']}", {"decision": "In Progress"}, 409, method="patch")
    assert call(w, f"/projects/{pid}/tasks", method="get")[0]["phase"] == 2
