"""Add a separate completed demo through real API operations; never reset records."""

from fastapi.testclient import TestClient
from app import main as m
from app.demo_assets import quotation_pdf, room_png


def seed_completed_demo(users):
    key = "yep-completed-portfolio-demo"
    if m.db.requests.find_one({"demo_key": key}):
        return
    clients = {}
    for name in ("owner", "customer", "worker"):
        c = TestClient(m.app)
        r = c.post(
            "/api/auth/login",
            json={"email": name + "@yep.local", "password": "Demo@12345"},
        )
        if r.status_code != 200:
            print(
                "Completed portfolio seed skipped: existing demo credentials changed; no accounts overwritten."
            )
            return
        clients[name] = c
    a, c, w = [clients[k] for k in ("owner", "customer", "worker")]

    def post(client, path, body=None):
        r = client.post("/api" + path, json=body)
        if r.status_code != 200:
            raise RuntimeError(path + ": " + r.text)
        return r.json()

    def file(client, name, content, mime):
        r = client.post("/api/files", files={"file": (name, content, mime)})
        r.raise_for_status()
        return r.json()["id"]

    r = post(
        c,
        "/requests",
        {
            "service": "Interior painting",
            "property_type": "Apartment",
            "location": "Demo studio, Pune",
            "area": 350,
            "rooms": 1,
            "description": "A separate completed demonstration of a warm studio finish.",
        },
    )
    m.db.requests.update_one({"id": r["id"]}, {"$set": {"demo_key": key}})
    post(
        a,
        f"/requests/{r['id']}/inspection",
        {
            "date": "2026-11-01",
            "measurements": "350 sq ft studio",
            "notes": "Suitable for surface preparation and painting",
            "completed": True,
        },
    )
    pdf = file(
        a,
        "completed-demo-quotation.pdf",
        quotation_pdf(1, "Studio finish", "12000", 5),
        "application/pdf",
    )
    q = post(
        a,
        f"/requests/{r['id']}/quotes",
        {
            "phase": 1,
            "title": "Studio finish",
            "description": "Prepare surfaces and apply warm interior finishes",
            "amount": "12000",
            "duration": 5,
            "pdf_id": pdf,
            "terms": "Demonstration scope and offline payments only",
        },
    )
    post(a, f"/quotes/{q['id']}/publish")
    post(c, f"/quotes/{q['id']}/decision", {"decision": "Accepted"})
    p = post(
        a,
        "/projects",
        {
            "quote_id": q["id"],
            "title": "Completed studio refresh · Demo",
            "manager_id": users["manager"]["id"],
            "start_date": "2026-11-02",
            "deadline": "2026-11-07",
        },
    )
    pid = p["id"]
    post(a, f"/projects/{pid}/workers", {"worker_id": users["worker"]["id"]})
    image = file(w, "completed-demo-illustration.png", room_png(), "image/png")
    message = post(
        w,
        f"/projects/{pid}/chat/internal",
        {
            "text": "Locally generated demonstration illustration of the finished room.",
            "file_id": image,
        },
    )
    post(
        a,
        f"/messages/{message['id']}/verify",
        {
            "approved": True,
            "share": True,
            "text": "Verified sample illustration for the completed demo project.",
        },
    )
    milestone = post(
        a,
        f"/projects/{pid}/milestones",
        {"title": "Preparation and finish", "phase": 1, "deadline": "2026-11-07"},
    )
    resp = a.patch(
        "/api/milestones/" + milestone["id"], json={"progress": 100, "publish": True}
    )
    resp.raise_for_status()
    post(
        a,
        f"/projects/{pid}/quality",
        {
            "title": "Final demo quality checklist",
            "passed": True,
            "items": [
                {"label": "Surface preparation", "passed": True},
                {"label": "Finish consistency", "passed": True},
                {"label": "Site clean-up", "passed": True},
            ],
        },
    )
    resp = a.patch(
        f"/api/projects/{pid}/phases/1",
        json={
            "title": "Studio finish",
            "start_date": "2026-11-02",
            "deadline": "2026-11-07",
            "status": "Completed",
        },
    )
    resp.raise_for_status()
    post(a, f"/projects/{pid}/complete")
    post(
        c,
        f"/projects/{pid}/feedback",
        {
            "rating": 5,
            "text": "Demonstration feedback: a careful and considered studio finish.",
        },
    )
    resp = a.put(
        f"/api/projects/{pid}/portfolio",
        json={
            "title": "Completed studio refresh · Demo",
            "description": "A completed Software Engineering demo project, shown with a locally generated room illustration. This is not a claim of real client work.",
            "category": "Interior painting",
            "file_ids": [image],
            "published": True,
            "show_feedback": True,
        },
    )
    resp.raise_for_status()
    m.db.projects.update_one({"id": pid}, {"$set": {"demo_key": key}})
