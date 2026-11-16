"""Idempotent, non-destructive demo seed. Requires a running local MongoDB."""

from pathlib import Path
import bcrypt
from fastapi.testclient import TestClient
from app import main as m
from app.demo_assets import quotation_pdf, room_png
from seed_portfolio import seed_completed_demo


def seed():
    m.db.command("ping")
    m.init_indexes()
    users = {}
    for email, name, role in [
        ("owner", "Ananya Rao", "ADMIN"),
        ("customer", "Alex Morgan", "CUSTOMER"),
        ("manager", "Rohan Shah", "MANAGER"),
        ("worker", "Dev Patel", "WORKER"),
    ]:
        found = m.db.users.find_one({"email": email + "@yep.local"})
        users[email] = (
            m.clean(found)
            if found
            else m.insert(
                "users",
                {
                    "email": email + "@yep.local",
                    "name": name,
                    "role": role,
                    "phone": "",
                    "address": "",
                    "active": True,
                    "password": bcrypt.hashpw(b"Demo@12345", bcrypt.gensalt()).decode(),
                },
            )
        )
    for name in [
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
        if not m.db.services.find_one({"name": name}):
            m.insert(
                "services",
                {
                    "name": name,
                    "description": f"Professional {name.lower()} with site assessment, careful preparation and a quality finish.",
                    "active": True,
                },
            )
    # Do not duplicate or reset demo records, even after they have been edited.
    if m.db.projects.find_one({"demo_key": "yep-initial-demo"}):
        seed_completed_demo(users)
        print("Demo data already exists; no records overwritten.")
        return
    if m.db.requests.find_one({"demo_key": "yep-initial-demo"}):
        print(
            "An interrupted demo seed exists. No duplicate records created. See README for a separate demo database."
        )
        return
    clients = {}
    for email in users:
        c = TestClient(m.app)
        r = c.post(
            "/api/auth/login",
            json={"email": email + "@yep.local", "password": "Demo@12345"},
        )
        if r.status_code != 200:
            raise RuntimeError(
                "Demo account password changed; seed leaves existing credentials untouched."
            )
        clients[email] = c
    a, c, manager, w = [clients[k] for k in ("owner", "customer", "manager", "worker")]

    def post(client, path, data=None):
        r = client.post("/api" + path, json=data)
        if r.status_code != 200:
            raise RuntimeError(f"{path}: {r.text}")
        return r.json()

    def file(client, name, content, mime):
        r = client.post("/api/files", files={"file": (name, content, mime)})
        if r.status_code != 200:
            raise RuntimeError(r.text)
        return r.json()["id"]

    photo = file(c, "demo-room-illustration.png", room_png(), "image/png")
    r = post(
        c,
        "/requests",
        {
            "service": "Interior painting",
            "property_type": "Apartment",
            "location": "Baner, Pune",
            "area": 1200,
            "rooms": 3,
            "description": "Refresh the living room and bedrooms with a warm, natural palette.",
            "preferred_date": "2026-11-20",
            "requirements": "Low odour finishes preferred.",
            "file_ids": [photo],
        },
    )
    m.db.requests.update_one(
        {"id": r["id"]}, {"$set": {"demo_key": "yep-initial-demo"}}
    )
    post(
        a,
        f"/requests/{r['id']}/inspection",
        {
            "date": "2026-11-16",
            "measurements": "1,200 sq ft apartment; three rooms.",
            "notes": "Walls are sound; minor filling and primer required.",
            "materials": "Primer, low-VOC emulsion and masking supplies.",
            "completed": True,
        },
    )

    def quote(phase, title, amount, duration):
        pdf = file(
            a,
            f"phase-{phase}-quotation.pdf",
            quotation_pdf(phase, title, amount, duration),
            "application/pdf",
        )
        q = post(
            a,
            f"/requests/{r['id']}/quotes",
            {
                "phase": phase,
                "title": title,
                "description": "Surface preparation, materials, skilled labour and finishing inspection.",
                "amount": amount,
                "duration": duration,
                "pdf_id": pdf,
                "terms": "Scope changes require a written revision. All payments are verified offline.",
            },
        )
        post(a, f"/quotes/{q['id']}/publish")
        return q

    q = quote(1, "Preparation & interior painting", "85000", 14)
    post(c, f"/quotes/{q['id']}/decision", {"decision": "Accepted"})
    p = post(
        a,
        "/projects",
        {
            "quote_id": q["id"],
            "title": "The Morgan residence",
            "manager_id": users["manager"]["id"],
            "start_date": "2026-11-20",
            "deadline": "2026-12-20",
        },
    )
    pid = p["id"]
    m.db.projects.update_one({"id": pid}, {"$set": {"demo_key": "yep-initial-demo"}})
    post(manager, f"/projects/{pid}/workers", {"worker_id": users["worker"]["id"]})
    for title, progress in [
        ("Site protection & preparation", 100),
        ("Surface repair & primer", 100),
        ("Interior painting", 35),
        ("Final finishing & quality review", 0),
    ]:
        milestone = post(
            a,
            f"/projects/{pid}/milestones",
            {
                "title": title,
                "phase": 1,
                "deadline": "2026-12-04",
                "description": "Reviewed by the project team before completion.",
            },
        )
        res = manager.patch(
            "/api/milestones/" + milestone["id"], json={"progress": progress}
        )
        res.raise_for_status()
    post(
        manager,
        f"/projects/{pid}/tasks",
        {
            "title": "Apply first coat in living room",
            "description": "Protect windows and flooring. Photograph the finished coat for review.",
            "worker_id": users["worker"]["id"],
            "deadline": "2026-11-27",
            "priority": "High",
        },
    )
    post(
        a,
        f"/projects/{pid}/chat/internal",
        {
            "text": "Welcome, team. Please post progress photographs here for verification."
        },
    )
    f = file(w, "verified-demo-room.png", room_png(), "image/png")
    message = post(
        w,
        f"/projects/{pid}/chat/internal",
        {
            "text": "Demo room illustration: surface preparation completed.",
            "file_id": f,
        },
    )
    post(
        manager,
        f"/messages/{message['id']}/verify",
        {
            "approved": True,
            "share": True,
            "text": "Surface preparation reviewed. This sample illustration demonstrates verified photo sharing.",
        },
    )
    post(
        w,
        f"/projects/{pid}/chat/internal",
        {
            "text": "First coat ready for review — demo illustration.",
            "file_id": file(w, "pending-demo-room.png", room_png(), "image/png"),
        },
    )
    post(
        c,
        f"/projects/{pid}/chat/customer",
        {"text": "Thank you! Please keep the living room in the warm neutral palette."},
    )
    quote(2, "Flooring & final details", "45000", 7)
    post(
        a,
        f"/projects/{pid}/payments",
        {
            "amount": "30000",
            "date": "2026-11-21",
            "method": "Bank Transfer",
            "reference": "DEMO-OFFLINE-001",
            "verification": "Demo: bank statement checked offline by Admin.",
            "notes": "Initial instalment",
            "idempotency_key": "seed-demo-payment-001",
        },
    )
    post(
        manager,
        f"/projects/{pid}/materials",
        {
            "name": "Low-VOC interior emulsion",
            "quantity": 40,
            "unit": "litres",
            "status": "Available",
            "notes": "Warm neutral palette.",
        },
    )
    post(
        manager,
        f"/projects/{pid}/quality",
        {
            "title": "Surface preparation review",
            "passed": True,
            "defects": "",
            "corrective_action": "Final finish review required after painting.",
        },
    )
    seed_completed_demo(users)
    print("Demo ready: customer / owner / manager / worker @yep.local | Demo@12345")


if __name__ == "__main__":
    seed()
