"""Additional public portfolio, scoped reports, assets and operational endpoints.
ctx is the existing application's module; database injection in tests is preserved.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import Depends
from fastapi.responses import FileResponse
from .models import PortfolioInput, MaterialInput, ProjectStatusInput
from .permissions import roles, project_access, execution


def install(app, ctx):
    @app.get("/api/dashboard")
    def dashboard(u=Depends(ctx.user)):
        projects = ctx.projects(u)
        ids = [p["id"] for p in projects]
        financial = u["role"] in ("ADMIN", "CUSTOMER")
        requests = (
            list(
                ctx.db.requests.find(
                    {} if u["role"] == "ADMIN" else {"customer_id": u["id"]}
                )
            )
            if financial
            else []
        )
        quotes = (
            list(
                ctx.db.quotes.find(
                    {}
                    if u["role"] == "ADMIN"
                    else {"customer_id": u["id"], "status": {"$ne": "Draft"}}
                )
            )
            if financial
            else []
        )
        tasks = list(
            ctx.db.tasks.find(
                {
                    "project_id": {"$in": ids},
                    **({"worker_id": u["id"]} if u["role"] == "WORKER" else {}),
                }
            )
        )
        today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
        recent = list(
            ctx.db.notifications.find({"user_id": u["id"]})
            .sort("created_at", -1)
            .limit(20)
        )
        result = {
            "stats": {
                "requests": len(requests),
                "pending_quotations": sum(q["status"] == "Published" for q in quotes),
                "active_projects": sum(p["status"] == "Active" for p in projects),
                "completed_projects": sum(p["status"] == "Completed" for p in projects),
                "pending_tasks": sum(t["status"] not in ("Completed",) for t in tasks),
                "completed_tasks": sum(t["status"] == "Completed" for t in tasks),
                "today_tasks": sum(
                    t["deadline"] <= today and t["status"] != "Completed" for t in tasks
                ),
                "unread_notifications": ctx.db.notifications.count_documents(
                    {"user_id": u["id"], "read": False}
                ),
            },
            "activity": [ctx.clean(n) for n in recent],
            "due_tasks": [
                ctx.clean(t)
                for t in tasks
                if t["deadline"] <= today and t["status"] != "Completed"
            ],
            "current_phases": [
                {
                    "project_id": p["id"],
                    "project_title": p["title"],
                    "phase": next(
                        (ph for ph in p["phases"] if ph["status"] == "Active"), None
                    ),
                }
                for p in projects
            ],
        }
        if u["role"] == "WORKER":
            result["instructions"] = [
                ctx.clean(m)
                for m in ctx.db.messages.find(
                    {
                        "project_id": {"$in": ids},
                        "channel": "internal",
                        "role": {"$in": ["ADMIN", "MANAGER"]},
                        "file_id": None,
                    }
                )
                .sort("created_at", -1)
                .limit(10)
            ]
        return result

    @app.get("/api/reports")
    def reports(u=Depends(ctx.user)):
        roles(u, "ADMIN", "MANAGER")
        projects = ctx.projects(u)
        ids = [p["id"] for p in projects]
        tasks = list(ctx.db.tasks.find({"project_id": {"$in": ids}}))
        issues = list(
            ctx.db.messages.find(
                {"project_id": {"$in": ids}, "channel": "internal", "issue": True}
            )
        )
        materials = list(ctx.db.materials.find({"project_id": {"$in": ids}}))
        return {
            "projects": [
                {
                    "id": p["id"],
                    "title": p["title"],
                    "status": p["status"],
                    "progress": p["progress"],
                    "deadline": p["deadline"],
                    "current_phase": next(
                        (ph["title"] for ph in p["phases"] if ph["status"] == "Active"),
                        "No active phase",
                    ),
                    "workers": len(p["worker_ids"]),
                }
                for p in projects
            ],
            "task_status": {
                s: sum(t["status"] == s for t in tasks)
                for s in ("Pending", "In Progress", "Blocked", "Completed")
            },
            "issues": [ctx.clean(x) for x in issues],
            "shortages": [ctx.clean(x) for x in materials if x["status"] == "Shortage"],
            "pending_evidence": ctx.db.messages.count_documents(
                {
                    "project_id": {"$in": ids},
                    "channel": "internal",
                    "verification": "Pending",
                }
            ),
            "monthly_project_activity": {
                month: sum(p["created_at"][:7] == month for p in projects)
                for month in sorted({p["created_at"][:7] for p in projects})
            },
        }

    @app.put("/api/materials/{mid}")
    def edit_material(mid: str, d: MaterialInput, u=Depends(ctx.user)):
        m = ctx.get("materials", mid)
        execution(u, ctx.get("projects", m["project_id"]))
        if d.status not in ("Required", "Available", "Shortage"):
            ctx.fail(422, "Invalid material status")
        ctx.db.materials.update_one(
            {"id": mid},
            {
                "$set": {
                    **d.model_dump(),
                    "updated_at": ctx.now(),
                    "updated_by": u["id"],
                }
            },
        )
        ctx.audit(u, "material_updated", mid)
        return {"ok": True}

    @app.patch("/api/projects/{pid}/status")
    def status(pid: str, d: ProjectStatusInput, u=Depends(ctx.user)):
        roles(u, "ADMIN")
        p = ctx.get("projects", pid)
        if p["status"] not in ("Active", "On Hold") or p["status"] == d.status:
            ctx.fail(409, "Invalid project transition")
        ctx.db.projects.update_one(
            {"id": pid, "status": p["status"]},
            {
                "$set": {"status": d.status},
                "$push": {
                    "status_history": {
                        "status": d.status,
                        "note": d.note,
                        "by": u["id"],
                        "date": ctx.now(),
                    }
                },
            },
        )
        ctx.audit(u, "project_status", pid)
        return {"ok": True}

    @app.get("/api/public/projects")
    def portfolio(category: str | None = None):
        rows = []
        for entry in ctx.db.portfolio.find(
            {"published": True, **({"category": category} if category else {})}
        ).sort("created_at", -1):
            p = ctx.db.projects.find_one(
                {"id": entry["project_id"], "status": "Completed"}
            )
            if not p:
                continue
            dto = {
                k: entry[k]
                for k in (
                    "id",
                    "project_id",
                    "title",
                    "description",
                    "category",
                    "file_ids",
                )
            }
            dto["completed_at"] = p.get("completed_at")
            dto["feedback"] = None
            if entry.get("show_feedback"):
                f = ctx.db.feedback.find_one({"project_id": p["id"]})
                if f:
                    dto["feedback"] = {"rating": f["rating"], "text": f["text"]}
            rows.append(dto)
        return rows

    @app.get("/api/projects/{pid}/portfolio")
    def portfolio_settings(pid: str, u=Depends(ctx.user)):
        roles(u, "ADMIN")
        ctx.get("projects", pid)
        entry = ctx.db.portfolio.find_one({"project_id": pid})
        return ctx.clean(entry) if entry else None

    @app.put("/api/projects/{pid}/portfolio")
    def publish_portfolio(pid: str, d: PortfolioInput, u=Depends(ctx.user)):
        roles(u, "ADMIN")
        p = ctx.get("projects", pid)
        if p["status"] != "Completed":
            ctx.fail(409, "Only completed projects can be published")
        for fid in d.file_ids:
            if not ctx.db.messages.find_one(
                {
                    "project_id": pid,
                    "channel": "customer",
                    "file_id": fid,
                    "verification": "Approved",
                }
            ):
                ctx.fail(
                    422, "Select only verified, customer-published progress photographs"
                )
        ctx.db.portfolio.update_one(
            {"project_id": pid},
            {
                "$set": {
                    **d.model_dump(),
                    "updated_at": ctx.now(),
                    "published_by": u["id"],
                },
                "$setOnInsert": {"id": str(ctx.uuid.uuid4()), "created_at": ctx.now()},
            },
            upsert=True,
        )
        ctx.audit(u, "portfolio_publication", pid)
        return {"ok": True}

    @app.get("/api/public/projects/{pid}/photos/{fid}")
    def portfolio_photo(pid: str, fid: str):
        if not ctx.db.projects.find_one(
            {"id": pid, "status": "Completed"}
        ) or not ctx.db.portfolio.find_one(
            {"project_id": pid, "published": True, "file_ids": fid}
        ):
            ctx.fail(404, "Public photograph not found")
        f = ctx.get("files", fid)
        return FileResponse(
            ctx.UPLOAD / (fid + f["ext"]),
            media_type="image/" + ("jpeg" if f["ext"] == ".jpg" else f["ext"][1:]),
        )

    @app.get("/api/public/services/{sid}/image")
    def service_image(sid: str):
        s = ctx.db.services.find_one({"id": sid, "active": True})
        if not s or not s.get("image_id"):
            ctx.fail(404, "Service image not found")
        f = ctx.get("files", s["image_id"])
        return FileResponse(
            ctx.UPLOAD / (f["id"] + f["ext"]),
            media_type="image/" + ("jpeg" if f["ext"] == ".jpg" else f["ext"][1:]),
        )

    from .models import PhaseCreate

    @app.post("/api/projects/{pid}/phases")
    def plan_phase(pid: str, d: PhaseCreate, u=Depends(ctx.user)):
        roles(u, "ADMIN")
        p = ctx.get("projects", pid)
        execution(u, p)
        if bool(d.start_date) != bool(d.deadline):
            ctx.fail(422, "Supply both phase dates, or leave both unscheduled")
        if d.start_date:
            ctx.valid_date(d.start_date)
            ctx.valid_date(d.deadline)
            if d.deadline < d.start_date:
                ctx.fail(422, "Deadline precedes start date")
        ph = {
            **d.model_dump(),
            "status": "Planned",
            "quote_id": None,
            "updated_by": u["id"],
            "updated_at": ctx.now(),
        }
        result = ctx.db.projects.update_one(
            {"id": pid, "phases.number": {"$ne": d.number}}, {"$push": {"phases": ph}}
        )
        if not result.modified_count:
            ctx.fail(409, "Phase number already exists")
        ctx.audit(u, "phase_planned", pid)
        return ph

    @app.get("/api/admin/customers/{uid}/history")
    def customer_history(uid: str, u=Depends(ctx.user)):
        roles(u, "ADMIN")
        c = ctx.get("users", uid)
        if c["role"] != "CUSTOMER":
            ctx.fail(422, "Select a Customer account")
        return {
            "customer": ctx.clean(c),
            "requests": [
                ctx.clean(r) for r in ctx.db.requests.find({"customer_id": uid})
            ],
            "projects": [
                ctx.clean(p) for p in ctx.db.projects.find({"customer_id": uid})
            ],
            "quotations": [
                ctx.clean(q) for q in ctx.db.quotes.find({"customer_id": uid})
            ],
        }

    from .models import SystemSettings

    @app.get("/api/settings/public")
    def public_settings():
        s = ctx.db.settings.find_one({"_id": "public"})
        return (
            {k: s[k] for k in ("business_name", "email", "phone", "location")}
            if s
            else {
                "business_name": "YEP",
                "email": None,
                "phone": "",
                "location": "Site visits are scheduled after request review.",
            }
        )

    @app.put("/api/admin/settings")
    def settings(d: SystemSettings, u=Depends(ctx.user)):
        roles(u, "ADMIN")
        ctx.db.settings.update_one(
            {"_id": "public"},
            {
                "$set": {
                    **d.model_dump(),
                    "updated_by": u["id"],
                    "updated_at": ctx.now(),
                }
            },
            upsert=True,
        )
        ctx.audit(u, "system_settings_updated", "public")
        return {"ok": True}

    @app.put("/api/admin/settings")
    def update_settings(d: SystemSettings, u=Depends(ctx.user)):
        roles(u, "ADMIN")
        ctx.db.settings.update_one(
            {"_id": "public"},
            {
                "$set": {
                    **d.model_dump(),
                    "updated_by": u["id"],
                    "updated_at": ctx.now(),
                }
            },
            upsert=True,
        )
        ctx.audit(u, "settings_updated", "public")
        return {"ok": True}
