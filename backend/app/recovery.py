"""Idempotent recovery of derived views from durable business records.
Source documents use conditional updates/unique keys. Derived project links, phases,
status history and customer milestone messages can be replayed after interruption.
No destructive data migration, standalone MongoDB compatible.
"""

from datetime import datetime, timezone


def stamp():
    return datetime.now(timezone.utc).isoformat()


def event(db, rid, key, status, note, by=None):
    entry = {"id": key, "status": status, "note": note, "date": stamp(), "by": by}
    db.requests.update_one(
        {"id": rid, "history.id": {"$ne": key}}, {"$push": {"history": entry}}
    )


def recover(db):
    for r in db.requests.find():
        event(
            db,
            r["id"],
            "submitted-" + r["id"],
            "Submitted",
            "Request received directly by Admin",
            r["customer_id"],
        )
    for ins in db.inspections.find():
        state = "Inspection Completed" if ins["completed"] else "Inspection Scheduled"
        event(
            db,
            ins["request_id"],
            ins["id"] + "-" + str(ins["completed"]),
            state,
            ins.get("notes", ""),
            ins.get("admin_id"),
        )
    for p in db.projects.find():
        db.quotes.update_many(
            {"request_id": p["request_id"]}, {"$set": {"project_id": p["id"]}}
        )
        # Progress is derived from exact milestone values, not rounded completion checks.
        ms = list(db.milestones.find({"project_id": p["id"]}))
        pct = sum(m["progress"] for m in ms) // len(ms) if ms else 0
        db.projects.update_one({"id": p["id"]}, {"$set": {"progress": pct}})
        event(
            db,
            p["request_id"],
            "project-" + p["id"],
            "Converted to Project",
            p["title"],
        )
    for q in db.quotes.find({"status": {"$ne": "Draft"}}):
        event(
            db,
            q["request_id"],
            "quote-" + q["id"] + "-Published",
            "Quotation Published",
            q.get("number", q["id"]),
        )
        if q["status"] != "Published":
            event(
                db,
                q["request_id"],
                "quote-" + q["id"] + "-" + q["status"],
                "Quotation " + q["status"],
                q.get("number", q["id"]),
            )
        if q.get("project_id") and q["status"] in ("Published", "Accepted"):
            phase = {
                "number": q["phase"],
                "title": q["title"],
                "duration": q["duration"],
                "status": "Planned",
                "start_date": "",
                "deadline": "",
                "quote_id": q["id"],
            }
            db.projects.update_one(
                {"id": q["project_id"], "phases.number": {"$ne": q["phase"]}},
                {"$push": {"phases": phase}},
            )
            db.projects.update_one(
                {
                    "id": q["project_id"],
                    "phases.number": q["phase"],
                    "phases.quote_id": {"$ne": q["id"]},
                },
                {
                    "$set": {
                        "phases.$.quote_id": q["id"],
                        "phases.$.duration": q["duration"],
                        "phases.$.title": q["title"],
                    }
                },
            )
    # An inspection write is authoritative even if the request's status update failed.
    for r in db.requests.find():
        p = db.projects.find_one({"request_id": r["id"]})
        q = db.quotes.find_one(
            {"request_id": r["id"], "phase": 1, "status": {"$ne": "Draft"}},
            sort=[("revision", -1)],
        )
        ins = db.inspections.find_one({"request_id": r["id"]})
        status = (
            "Converted to Project"
            if p
            else (
                "Approved" if q["status"] == "Accepted" else "Quotation " + q["status"]
            )
            if q
            else "Inspection Completed"
            if ins and ins["completed"]
            else None
        )
        if status:
            db.requests.update_one({"id": r["id"]}, {"$set": {"status": status}})
    for m in db.milestones.find({"published_update": {"$exists": True}}):
        v = m["published_update"]
        key = "milestone-" + m["id"] + "-" + v["at"]
        payload = {
            "id": key,
            "created_at": v["at"],
            "project_id": m["project_id"],
            "channel": "customer",
            "sender_id": v["by"],
            "sender_name": v["name"],
            "role": v["role"],
            "text": f"Verified milestone: {m['title']} — {v['progress']}% complete",
            "file_id": None,
            "milestone_id": m["id"],
            "verification": "Approved",
        }
        db.messages.update_one({"id": key}, {"$setOnInsert": payload}, upsert=True)
