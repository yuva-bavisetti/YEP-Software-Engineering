from .quotations import cents, quotation_total
from .models import RequestReply
from .permissions import (
    roles,
    project_access,
    execution,
    financial,
    request_access,
    channel_access,
)
import os, secrets, hashlib, uuid, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import bcrypt
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .models import (
    Login,
    Register,
    RequestInput,
    InspectionInput,
    QuoteInput,
    Decision,
    ProjectInput,
    Assignment,
    MilestoneInput,
    Progress,
    TaskInput,
    MessageInput,
    Verify,
    PaymentInput,
    Profile,
    Employee,
    Feedback,
    PhaseInput,
    Reassign,
    ServiceInput,
    RequestStatus,
    MaterialInput,
    QualityInput,
    Enquiry,
)
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError

load_dotenv()
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    init_indexes()
    yield


app = FastAPI(title="YEP API", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
client = MongoClient(
    os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017"), serverSelectionTimeoutMS=3000
)
db = client[os.getenv("MONGO_DB", "yep")]
UPLOAD = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def fail(code, msg):
    raise HTTPException(code, msg)


def clean(d):
    return {k: v for k, v in d.items() if k not in ("_id", "password", "token")}


def get(col, id):
    d = db[col].find_one({"id": id})
    if not d:
        fail(404, "Record not found")
    return d


def insert(col, data):
    d = {"id": str(uuid.uuid4()), "created_at": now(), **data}
    db[col].insert_one(d)
    return clean(d)


def audit(u, action, target):
    insert("activity", {"user_id": u["id"], "action": action, "target": target})


def notify(uid, text):
    insert("notifications", {"user_id": uid, "text": text, "read": False})


def init_indexes():
    for col in [
        "users",
        "sessions",
        "requests",
        "inspections",
        "quotes",
        "projects",
        "messages",
        "files",
        "payments",
        "tasks",
        "milestones",
        "notifications",
        "activity",
        "services",
        "feedback",
        "enquiries",
        "materials",
        "quality",
    ]:
        db[col].create_index("id", unique=True)
    db.users.create_index("email", unique=True)
    db.sessions.create_index("token", unique=True)
    db.projects.create_index("request_id", unique=True)
    db.quotes.create_index(
        [("request_id", 1), ("phase", 1), ("revision", 1)], unique=True
    )
    db.payments.create_index([("project_id", 1), ("idempotency_key", 1)], unique=True)
    db.messages.create_index([("project_id", 1), ("channel", 1), ("created_at", 1)])
    db.messages.create_index("source_id", unique=True, sparse=True)
    db.inspections.create_index("request_id", unique=True)
    db.feedback.create_index([("project_id", 1), ("customer_id", 1)], unique=True)
    db.files.create_index("owner_id")
    db.tasks.create_index("worker_id")


def user(request: Request):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin and origin not in (
            os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
            "http://localhost:8000",
        ):
            fail(403, "Untrusted origin")
    token = request.cookies.get("yep_session", "")
    s = db.sessions.find_one({"token": hashlib.sha256(token.encode()).hexdigest()})
    if not s or s["expires"] < now():
        fail(401, "Please sign in")
    u = get("users", s["user_id"])
    if not u.get("active", True):
        fail(403, "Account inactive")
    return u


def owned_files(u, ids, kind=None):
    for id in ids:
        f = get("files", id)
        if f["owner_id"] != u["id"] or (kind and f["kind"] != kind):
            fail(403, "Invalid attachment")
        if (
            db.requests.find_one({"file_ids": id})
            or db.inspections.find_one({"file_ids": id})
            or db.quotes.find_one({"pdf_id": id})
            or db.messages.find_one({"file_id": id})
        ):
            fail(409, "Attachment already linked")


def valid_date(s):
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        fail(422, "Use a valid YYYY-MM-DD date")


@app.get("/api/health")
def health():
    db.command("ping")
    return {"status": "ok", "database": "MongoDB"}


@app.post("/api/auth/register")
def register(d: Register):
    if len(d.password) < 10 or len(d.password.encode()) > 72:
        fail(422, "Password must have 10–72 bytes")
    try:
        return insert(
            "users",
            {
                "name": d.name,
                "email": d.email.lower(),
                "phone": d.phone,
                "role": "CUSTOMER",
                "active": True,
                "password": bcrypt.hashpw(
                    d.password.encode(), bcrypt.gensalt()
                ).decode(),
            },
        )
    except DuplicateKeyError:
        fail(409, "Email already registered")


@app.post("/api/auth/login")
def login(d: Login, response: Response):
    u = db.users.find_one({"email": d.email.lower()})
    if len(d.password.encode()) > 72:
        fail(401, "Invalid email or password")
    if (
        not u
        or not u.get("active", True)
        or not bcrypt.checkpw(d.password.encode(), u["password"].encode())
    ):
        fail(401, "Invalid email or password")
    token = secrets.token_urlsafe(48)
    insert(
        "sessions",
        {
            "token": hashlib.sha256(token.encode()).hexdigest(),
            "user_id": u["id"],
            "expires": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        },
    )
    response.set_cookie(
        "yep_session",
        token,
        httponly=True,
        samesite="lax",
        secure=os.getenv("COOKIE_SECURE") == "true",
        max_age=604800,
    )
    return clean(u)


@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    db.sessions.delete_one(
        {
            "token": hashlib.sha256(
                request.cookies.get("yep_session", "").encode()
            ).hexdigest()
        }
    )
    response.delete_cookie("yep_session")
    return {"ok": True}


@app.get("/api/auth/me")
def me(u=Depends(user)):
    return clean(u)


@app.get("/api/services")
def services():
    return [clean(d) for d in db.services.find({"active": True})]


@app.post("/api/enquiries")
def enquiry(d: Enquiry):
    return insert("enquiries", d.model_dump())


@app.get("/api/users")
def users(u=Depends(user)):
    roles(u, "ADMIN", "MANAGER")
    return [
        {
            k: d.get(k)
            for k in (
                ("id", "name", "role", "active", "email", "phone")
                if u["role"] == "ADMIN"
                else ("id", "name", "role", "active")
            )
        }
        for d in db.users.find({"role": {"$in": ["MANAGER", "WORKER"]}})
    ]


@app.post("/api/requests")
def create_request(d: RequestInput, u=Depends(user)):
    roles(u, "CUSTOMER")
    if d.preferred_date:
        valid_date(d.preferred_date)
    if not db.services.find_one({"name": d.service, "active": True}):
        fail(422, "Select an available service")
    owned_files(u, d.file_ids)
    r = insert(
        "requests",
        {
            **d.model_dump(),
            "customer_id": u["id"],
            "customer_name": u["name"],
            "status": "Submitted",
        },
    )
    for a in db.users.find({"role": "ADMIN"}):
        notify(a["id"], "New customer request: " + d.service)
    audit(u, "request_created", r["id"])
    return r


@app.get("/api/requests")
def requests(u=Depends(user)):
    roles(u, "ADMIN", "CUSTOMER")
    return [
        clean(d)
        for d in db.requests.find(
            {} if u["role"] == "ADMIN" else {"customer_id": u["id"]}
        )
    ]


@app.get("/api/requests/{rid}/inspection")
def inspection(rid: str, u=Depends(user)):
    r = get("requests", rid)
    request_access(u, r)
    d = db.inspections.find_one({"request_id": rid})
    return clean(d) if d else None


@app.post("/api/requests/{rid}/inspection")
def inspect(rid: str, d: InspectionInput, u=Depends(user)):
    roles(u, "ADMIN")
    get("requests", rid)
    owned_files(u, d.file_ids, "image")
    valid_date(d.date[:10])
    existing = db.inspections.find_one({"request_id": rid})
    if existing and existing.get("completed"):
        fail(409, "Completed inspection is immutable")
    payload = {**d.model_dump(), "admin_id": u["id"], "updated_at": now()}
    db.inspections.update_one(
        {"request_id": rid},
        {
            "$set": payload,
            "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now()},
        },
        upsert=True,
    )
    db.requests.update_one(
        {"id": rid},
        {
            "$set": {
                "status": "Inspection Completed"
                if d.completed
                else "Inspection Scheduled"
            }
        },
    )
    audit(u, "inspection_recorded", rid)
    return {"ok": True}


@app.post("/api/requests/{rid}/quotes")
def create_quote(rid: str, d: QuoteInput, u=Depends(user)):
    roles(u, "ADMIN")
    r = get("requests", rid)
    if not db.inspections.find_one({"request_id": rid, "completed": True}):
        fail(409, "Complete the initial inspection first")
    p = db.projects.find_one({"request_id": rid})
    if p and p["status"] == "Completed":
        fail(409, "Completed projects cannot receive new quotations")
    if d.phase > 1 and not p:
        fail(409, "Create the project before subsequent phases")
    if d.phase == 1 and p:
        fail(409, "Initial phase is already contracted")
    owned_files(u, [d.pdf_id], "pdf")
    prev = db.quotes.find_one(
        {"request_id": rid, "phase": d.phase}, sort=[("revision", -1)]
    )
    if prev and prev["status"] not in ("Revision Requested", "Rejected"):
        fail(409, "Decide the existing quotation before revising")
    rev = prev["revision"] + 1 if prev else 1
    try:
        q = insert(
            "quotes",
            {
                "request_id": rid,
                "project_id": p["id"] if p else None,
                "customer_id": r["customer_id"],
                "phase": d.phase,
                "revision": rev,
                "number": f"YQ-{rid[:6]}-{d.phase}-R{rev}",
                "title": d.title,
                "description": d.description,
                "amount_cents": quotation_total(d),
                "items": [
                    {
                        "description": i.description,
                        "category": i.category,
                        "quantity": str(i.quantity),
                        "unit": i.unit,
                        "unit_price_cents": cents(i.unit_price),
                        "total_cents": cents(i.quantity * i.unit_price),
                    }
                    for i in d.items
                ],
                "tax_percent": str(d.tax_percent),
                "discount_cents": cents(d.discount),
                "duration": d.duration,
                "pdf_id": d.pdf_id,
                "terms": d.terms,
                "status": "Draft",
            },
        )
    except DuplicateKeyError:
        fail(409, "Concurrent revision; reload quotations")
    audit(u, "quote_drafted", q["id"])
    return q


@app.get("/api/quotes")
def quotes(u=Depends(user)):
    roles(u, "ADMIN", "CUSTOMER")
    query = (
        {}
        if u["role"] == "ADMIN"
        else {"customer_id": u["id"], "status": {"$ne": "Draft"}}
    )
    return [clean(d) for d in db.quotes.find(query)]


@app.post("/api/quotes/{qid}/publish")
def publish(qid: str, u=Depends(user)):
    roles(u, "ADMIN")
    q = get("quotes", qid)
    if not db.inspections.find_one({"request_id": q["request_id"], "completed": True}):
        fail(409, "Inspection required")
    if not db.quotes.update_one(
        {"id": qid, "status": "Draft"},
        {"$set": {"status": "Published", "published_at": now()}},
    ).modified_count:
        fail(409, "Quotation already published")
    if q["project_id"]:
        db.projects.update_one(
            {"id": q["project_id"], "phases.number": q["phase"]},
            {
                "$set": {
                    "phases.$.title": q["title"],
                    "phases.$.duration": q["duration"],
                    "phases.$.quote_id": qid,
                }
            },
        )
        db.projects.update_one(
            {"id": q["project_id"], "phases.number": {"$ne": q["phase"]}},
            {
                "$push": {
                    "phases": {
                        "number": q["phase"],
                        "title": q["title"],
                        "duration": q["duration"],
                        "status": "Planned",
                        "start_date": "",
                        "deadline": "",
                        "quote_id": qid,
                    }
                }
            },
        )
    if not q["project_id"]:
        db.requests.update_one(
            {"id": q["request_id"]}, {"$set": {"status": "Quotation Published"}}
        )
    notify(q["customer_id"], "A phase quotation is ready for your review")
    audit(u, "quote_published", qid)
    return {"ok": True}


@app.post("/api/quotes/{qid}/decision")
def decision(qid: str, d: Decision, u=Depends(user)):
    roles(u, "CUSTOMER")
    q = get("quotes", qid)
    financial(u, q["customer_id"])
    if d.decision not in ("Accepted", "Rejected", "Revision Requested"):
        fail(422, "Invalid decision")
    if not db.quotes.update_one(
        {"id": qid, "status": "Published"},
        {"$set": {"status": d.decision, "decided_at": now()}},
    ).modified_count:
        fail(409, "Quotation has already been decided")
    if q["phase"] == 1 and not q["project_id"]:
        db.requests.update_one(
            {"id": q["request_id"]},
            {
                "$set": {
                    "status": "Approved"
                    if d.decision == "Accepted"
                    else "Quotation " + d.decision
                }
            },
        )
    for a in db.users.find({"role": "ADMIN"}):
        notify(a["id"], "Customer quotation decision: " + d.decision)
    audit(u, "quote_" + d.decision, qid)
    return {"ok": True}


@app.post("/api/projects")
def create_project(d: ProjectInput, u=Depends(user)):
    roles(u, "ADMIN")
    q = get("quotes", d.quote_id)
    if q["phase"] != 1 or q["status"] != "Accepted":
        fail(409, "Phase 1 customer acceptance is required")
    m = get("users", d.manager_id)
    if m["role"] != "MANAGER" or not m.get("active"):
        fail(422, "Select an active manager")
    valid_date(d.start_date)
    valid_date(d.deadline)
    if d.deadline < d.start_date:
        fail(422, "Deadline precedes start date")
    r = get("requests", q["request_id"])
    try:
        p = insert(
            "projects",
            {
                "request_id": r["id"],
                "initial_quote_id": q["id"],
                "customer_id": r["customer_id"],
                "customer_name": r["customer_name"],
                "title": d.title,
                "location": r["location"],
                "manager_id": d.manager_id,
                "worker_ids": [],
                "start_date": d.start_date,
                "deadline": d.deadline,
                "status": "Active",
                "progress": 0,
                "channels": ["internal", "customer"],
                "phases": [
                    {
                        "number": 1,
                        "title": q["title"],
                        "duration": q["duration"],
                        "start_date": d.start_date,
                        "deadline": d.deadline,
                        "status": "Active",
                        "quote_id": q["id"],
                    }
                ],
            },
        )
    except DuplicateKeyError:
        fail(409, "A project already exists for this request")
    db.quotes.update_many({"request_id": r["id"]}, {"$set": {"project_id": p["id"]}})
    db.requests.update_one(
        {"id": r["id"]}, {"$set": {"status": "Converted to Project"}}
    )
    notify(d.manager_id, "You have been assigned " + d.title)
    audit(u, "project_created", p["id"])
    return p


@app.get("/api/projects")
def projects(u=Depends(user)):
    query = (
        {}
        if u["role"] == "ADMIN"
        else {"customer_id": u["id"]}
        if u["role"] == "CUSTOMER"
        else {"manager_id": u["id"]}
        if u["role"] == "MANAGER"
        else {"worker_ids": u["id"]}
    )
    result = []
    for p in db.projects.find(query):
        p = clean(p)
        if u["role"] in ("MANAGER", "WORKER"):
            p.pop("initial_quote_id", None)
            for phase in p["phases"]:
                phase.pop("quote_id", None)
            p["phases"] = [
                {k: v for k, v in phase.items() if k != "quote_id"}
                for phase in p["phases"]
            ]
        if u["role"] == "WORKER":
            p.pop("customer_id", None)
            p.pop("customer_name", None)
        manager = db.users.find_one({"id": p.get("manager_id")})
        p["manager_name"] = manager["name"] if manager else "Not assigned"
        p["team"] = [
            {"id": w["id"], "name": w["name"]}
            for w in db.users.find({"id": {"$in": p.get("worker_ids", [])}})
        ]
        result.append(p)
    return result


@app.post("/api/projects/{pid}/workers")
def assign(pid: str, d: Assignment, u=Depends(user)):
    p = get("projects", pid)
    execution(u, p)
    w = get("users", d.worker_id)
    if w["role"] != "WORKER" or not w.get("active"):
        fail(422, "Select an active worker")
    db.projects.update_one({"id": pid}, {"$addToSet": {"worker_ids": d.worker_id}})
    notify(d.worker_id, "Assigned to " + p["title"])
    audit(u, "worker_assigned", pid)
    return {"ok": True}


@app.get("/api/projects/{pid}/milestones")
def milestones(pid: str, u=Depends(user)):
    project_access(u, get("projects", pid))
    return [clean(d) for d in db.milestones.find({"project_id": pid})]


@app.post("/api/projects/{pid}/milestones")
def milestone(pid: str, d: MilestoneInput, u=Depends(user)):
    p = get("projects", pid)
    execution(u, p)
    valid_date(d.deadline)
    if d.phase not in [v["number"] for v in p["phases"]]:
        fail(422, "Phase not found")
    return insert(
        "milestones",
        {**d.model_dump(), "project_id": pid, "progress": 0, "updated_by": u["id"]},
    )


@app.patch("/api/milestones/{mid}")
def progress(mid: str, d: Progress, u=Depends(user)):
    m = get("milestones", mid)
    p = get("projects", m["project_id"])
    execution(u, p)
    db.milestones.update_one(
        {"id": mid},
        {"$set": {"progress": d.progress, "updated_by": u["id"], "updated_at": now()}},
    )
    allm = list(db.milestones.find({"project_id": p["id"]}))
    pct = round(sum(m["progress"] for m in allm) / len(allm))
    db.projects.update_one({"id": p["id"]}, {"$set": {"progress": pct}})
    audit(u, "milestone_updated", mid)
    return {"ok": True}


@app.post("/api/projects/{pid}/complete")
def complete(pid: str, u=Depends(user)):
    p = get("projects", pid)
    execution(u, p)
    if any(phase["status"] != "Completed" for phase in p["phases"]):
        fail(409, "Mark all project phases completed first")
    if p["progress"] != 100 or not db.milestones.count_documents({"project_id": pid}):
        fail(409, "Complete all milestones first")
    if db.tasks.count_documents({"project_id": pid, "status": {"$ne": "Completed"}}):
        fail(409, "Complete all tasks first")
    latest_quality = db.quality.find_one({"project_id": pid}, sort=[("created_at", -1)])
    if not latest_quality or not latest_quality["passed"]:
        fail(409, "Record a passed quality inspection before completion")
    db.projects.update_one(
        {"id": pid},
        {
            "$set": {
                "status": "Completed",
                "completed_at": now(),
                "quality_passed_by": u["id"],
            }
        },
    )
    audit(u, "quality_checked_and_completed", pid)
    return {"ok": True}


@app.get("/api/projects/{pid}/tasks")
def tasks(pid: str, u=Depends(user)):
    project_access(u, get("projects", pid))
    query = {"project_id": pid}
    if u["role"] == "WORKER":
        query["worker_id"] = u["id"]
    return [clean(d) for d in db.tasks.find(query)]


@app.post("/api/projects/{pid}/tasks")
def task(pid: str, d: TaskInput, u=Depends(user)):
    p = get("projects", pid)
    execution(u, p)
    valid_date(d.deadline)
    if d.worker_id not in p["worker_ids"]:
        fail(422, "Assign this worker to the project first")
    return insert("tasks", {**d.model_dump(), "project_id": pid, "status": "Pending"})


@app.patch("/api/tasks/{tid}")
def task_status(tid: str, d: Decision, u=Depends(user)):
    t = get("tasks", tid)
    p = get("projects", t["project_id"])
    project_access(u, p)
    if u["role"] == "CUSTOMER" or (u["role"] == "WORKER" and t["worker_id"] != u["id"]):
        fail(403, "Not your task")
    if d.decision not in ("Pending", "In Progress", "Completed", "Blocked"):
        fail(422, "Invalid status")
    db.tasks.update_one(
        {"id": tid}, {"$set": {"status": d.decision, "updated_at": now()}}
    )
    return {"ok": True}


@app.get("/api/projects/{pid}/chat/{channel}")
def messages(pid: str, channel: str, u=Depends(user)):
    channel_access(u, get("projects", pid), channel)
    if channel == "customer":
        for source in db.messages.find(
            {
                "project_id": pid,
                "channel": "internal",
                "published": True,
                "verification": "Approved",
            }
        ):
            ensure_shared_message(source)
    return [
        clean(d)
        for d in db.messages.find({"project_id": pid, "channel": channel}).sort(
            "created_at", 1
        )
    ]


@app.post("/api/projects/{pid}/chat/{channel}")
def message(pid: str, channel: str, d: MessageInput, u=Depends(user)):
    channel_access(u, get("projects", pid), channel)
    if not d.text and not d.file_id:
        fail(422, "Enter a message or attach an image")
    if d.file_id:
        owned_files(u, [d.file_id], "image")
    result = insert(
        "messages",
        {
            "project_id": pid,
            "channel": channel,
            "sender_id": u["id"],
            "sender_name": u["name"],
            "role": u["role"],
            "text": d.text,
            "file_id": d.file_id,
            "issue": d.issue,
            "verification": "Pending" if channel == "internal" and d.file_id else None,
        },
    )

    p = get("projects", pid)
    recipients = {
        p.get("manager_id"),
        *(p["worker_ids"] if channel == "internal" else [p["customer_id"]]),
    }
    recipients.update(a["id"] for a in db.users.find({"role": "ADMIN"}))
    for uid in recipients - {u["id"], None}:
        notify(uid, "New " + channel + " project message: " + p["title"])
    return result


@app.post("/api/messages/{mid}/verify")
def verify(mid: str, d: Verify, u=Depends(user)):
    m = get("messages", mid)
    p = get("projects", m["project_id"])
    execution(u, p)
    if m["channel"] != "internal" or not m.get("file_id"):
        fail(422, "Select internal photo evidence")
    if d.share and not d.approved:
        fail(422, "Only approved evidence can be shared")
    update = {
        "verification": "Approved" if d.approved else "Rejected",
        "verified_by": u["id"],
        "verified_at": now(),
    }
    if d.share:
        update.update({"published": True, "share_text": d.text or m["text"]})
    result = db.messages.find_one_and_update(
        {"id": mid, "verification": "Pending"},
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        fail(409, "Evidence already reviewed")
    if d.share:
        ensure_shared_message({**result, "share_text": d.text or m["text"]}, u)
    audit(u, "progress_verified", mid)
    return {"ok": True}


@app.get("/api/projects/{pid}/finance")
def finance(pid: str, u=Depends(user)):
    p = get("projects", pid)
    financial(u, p["customer_id"])
    qs = list(
        db.quotes.find(
            {
                "request_id": p["request_id"],
                "status": {"$in": ["Published", "Accepted"]},
            }
        )
    )
    # Published subsequent phase quotations are payable; superseded/rejected revisions are excluded.
    total = sum(q["amount_cents"] for q in qs)
    payments = [clean(d) for d in db.payments.find({"project_id": pid})]
    paid = sum(v["amount_cents"] for v in payments)
    return {
        "total_cents": total,
        "paid_cents": paid,
        "balance_cents": total - paid,
        "payments": payments,
    }


@app.post("/api/projects/{pid}/payments")
def payment(pid: str, d: PaymentInput, u=Depends(user)):
    roles(u, "ADMIN")
    get("projects", pid)
    valid_date(d.date)
    if d.method not in ("Cash", "UPI", "Bank Transfer", "Other"):
        fail(422, "Invalid payment method")
    try:
        result = insert(
            "payments",
            {
                **d.model_dump(exclude={"amount"}),
                "amount_cents": cents(d.amount),
                "project_id": pid,
                "verified_by": u["id"],
            },
        )
    except DuplicateKeyError:
        fail(409, "Payment already recorded")
    notify(
        get("projects", pid)["customer_id"],
        "An offline-verified payment has been added to your project",
    )
    audit(u, "offline_payment_verified", result["id"])
    return result


@app.post("/api/payments/{payment_id}/reverse")
def reverse(payment_id: str, d: MessageInput, u=Depends(user)):
    roles(u, "ADMIN")
    p = get("payments", payment_id)
    if not d.text or p["amount_cents"] <= 0:
        fail(422, "A correction reason and original payment are required")
    try:
        r = insert(
            "payments",
            {
                "project_id": p["project_id"],
                "amount_cents": -p["amount_cents"],
                "idempotency_key": "reverse-" + payment_id,
                "reverses": payment_id,
                "notes": d.text,
                "verified_by": u["id"],
                "date": now()[:10],
                "method": p["method"],
            },
        )
    except DuplicateKeyError:
        fail(409, "Payment already reversed")
    audit(u, "payment_reversed", payment_id)
    return r


@app.post("/api/files")
async def upload(file: UploadFile = File(...), u=Depends(user)):
    data = await file.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        fail(422, "Maximum file size is 10 MB")
    if data.startswith(b"%PDF-"):
        kind, ext = "pdf", ".pdf"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        kind, ext = "image", ".png"
    elif data.startswith(b"\xff\xd8\xff"):
        kind, ext = "image", ".jpg"
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        kind, ext = "image", ".webp"
    else:
        fail(422, "Upload a PDF, PNG, JPEG or WebP file")
    if kind == "pdf":
        roles(u, "ADMIN")
    id = str(uuid.uuid4())
    (UPLOAD / (id + ext)).write_bytes(data)
    return insert(
        "files",
        {
            "id": id,
            "owner_id": u["id"],
            "name": Path(file.filename or "attachment").name,
            "kind": kind,
            "ext": ext,
            "size": len(data),
        },
    )


@app.get("/api/files/{fid}")
def download(fid: str, u=Depends(user)):
    f = get("files", fid)
    allowed = False
    q = db.quotes.find_one({"pdf_id": fid})
    if q:
        financial(u, q["customer_id"])
        allowed = u["role"] == "ADMIN" or q["status"] != "Draft"
    else:
        for m in db.messages.find({"file_id": fid}):
            try:
                channel_access(u, get("projects", m["project_id"]), m["channel"])
                allowed = True
                break
            except HTTPException:
                pass
        r = db.requests.find_one({"file_ids": fid})
        ins = db.inspections.find_one({"file_ids": fid})
        if ins:
            r = get("requests", ins["request_id"])
        if r:
            request_access(u, r)
            allowed = True
        if not q and not r and not db.messages.find_one({"file_id": fid}):
            allowed = f["owner_id"] == u["id"]
    if not allowed:
        fail(403, "Private attachment")
    return FileResponse(
        UPLOAD / (fid + f["ext"]),
        filename=f["name"],
        media_type="application/pdf"
        if f["kind"] == "pdf"
        else "image/" + ("jpeg" if f["ext"] == ".jpg" else f["ext"][1:]),
        content_disposition_type="inline",
    )


@app.get("/api/notifications")
def notifications(u=Depends(user)):
    return [
        clean(d)
        for d in db.notifications.find({"user_id": u["id"]})
        .sort("created_at", -1)
        .limit(50)
    ]


@app.get("/api/activity")
def activity(u=Depends(user)):
    roles(u, "ADMIN")
    return [clean(d) for d in db.activity.find().sort("created_at", -1).limit(100)]


@app.patch("/api/profile")
def profile(d: Profile, u=Depends(user)):
    data = d.model_dump(exclude={"password", "email"})
    if d.email:
        existing = db.users.find_one({"email": d.email.lower(), "id": {"$ne": u["id"]}})
        if existing:
            fail(409, "Email is already registered")
        data["email"] = d.email.lower()
    if d.password:
        if len(d.password) < 10 or len(d.password.encode()) > 72:
            fail(422, "Password must have 10–72 bytes")
        data["password"] = bcrypt.hashpw(d.password.encode(), bcrypt.gensalt()).decode()
    db.users.update_one({"id": u["id"]}, {"$set": data})
    return clean(get("users", u["id"]))


@app.post("/api/users")
def employee(d: Employee, u=Depends(user)):
    roles(u, "ADMIN")
    if d.role not in ("MANAGER", "WORKER"):
        fail(422, "Invalid employee role")
    if len(d.password) < 10 or len(d.password.encode()) > 72:
        fail(422, "Use a password of 10–72 bytes")
    try:
        return insert(
            "users",
            {
                "name": d.name,
                "email": d.email.lower(),
                "phone": d.phone,
                "role": d.role,
                "active": True,
                "password": bcrypt.hashpw(
                    d.password.encode(), bcrypt.gensalt()
                ).decode(),
            },
        )
    except DuplicateKeyError:
        fail(409, "Email already exists")


@app.patch("/api/users/{uid}/active")
def activate(uid: str, d: Decision, u=Depends(user)):
    roles(u, "ADMIN")
    target = get("users", uid)
    if target["role"] == "ADMIN":
        fail(403, "Cannot deactivate administrators")
    if d.decision not in ("active", "inactive"):
        fail(422, "Invalid state")
    db.users.update_one({"id": uid}, {"$set": {"active": d.decision == "active"}})
    audit(u, "account_status", uid)
    return {"ok": True}


@app.post("/api/projects/{pid}/feedback")
def feedback(pid: str, d: Feedback, u=Depends(user)):
    roles(u, "CUSTOMER")
    p = get("projects", pid)
    project_access(u, p)
    if p["status"] != "Completed":
        fail(409, "Complete the project first")
    db.feedback.update_one(
        {"project_id": pid, "customer_id": u["id"]},
        {
            "$set": {**d.model_dump(), "updated_at": now()},
            "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now()},
        },
        upsert=True,
    )
    return {"ok": True}


@app.patch("/api/projects/{pid}/phases/{number}")
def phase_update(pid: str, number: int, d: PhaseInput, u=Depends(user)):
    p = get("projects", pid)
    execution(u, p)
    valid_date(d.start_date)
    valid_date(d.deadline)
    if d.deadline < d.start_date or d.status not in ("Planned", "Active", "Completed"):
        fail(422, "Invalid phase dates or status")
    result = db.projects.update_one(
        {"id": pid, "phases.number": number},
        {
            "$set": {
                "phases.$.title": d.title,
                "phases.$.start_date": d.start_date,
                "phases.$.deadline": d.deadline,
                "phases.$.status": d.status,
            }
        },
    )
    if not result.matched_count:
        fail(404, "Phase not found")
    audit(u, "phase_updated", pid)
    return {"ok": True}


@app.patch("/api/projects/{pid}/manager")
def reassign(pid: str, d: Reassign, u=Depends(user)):
    roles(u, "ADMIN")
    get("projects", pid)
    m = get("users", d.manager_id)
    if m["role"] != "MANAGER" or not m["active"]:
        fail(422, "Select an active manager")
    db.projects.update_one({"id": pid}, {"$set": {"manager_id": d.manager_id}})
    audit(u, "manager_assigned", pid)
    return {"ok": True}


@app.post("/api/services")
def add_service(d: ServiceInput, u=Depends(user)):
    roles(u, "ADMIN")
    return insert("services", d.model_dump())


@app.put("/api/services/{sid}")
def edit_service(sid: str, d: ServiceInput, u=Depends(user)):
    roles(u, "ADMIN")
    get("services", sid)
    db.services.update_one({"id": sid}, {"$set": d.model_dump()})
    return {"ok": True}


@app.patch("/api/requests/{rid}/status")
def request_status(rid: str, d: RequestStatus, u=Depends(user)):
    roles(u, "ADMIN")
    r = get("requests", rid)
    if d.status not in ("Under Review", "More Information Required", "Rejected"):
        fail(422, "Invalid review status")
    if db.projects.find_one({"request_id": rid}) or db.quotes.find_one(
        {"request_id": rid}
    ):
        fail(409, "Review is locked after quotation preparation")
    db.requests.update_one(
        {"id": rid},
        {
            "$set": {"status": d.status},
            "$push": {
                "history": {
                    "status": d.status,
                    "note": d.note,
                    "date": now(),
                    "by": u["id"],
                }
            },
        },
    )
    notify(r["customer_id"], d.status + ": " + d.note)
    audit(u, "request_review", rid)
    return {"ok": True}


@app.get("/api/projects/{pid}/materials")
def materials(pid: str, u=Depends(user)):
    p = get("projects", pid)
    project_access(u, p)
    roles(u, "ADMIN", "MANAGER", "WORKER")
    return [clean(d) for d in db.materials.find({"project_id": pid})]


@app.post("/api/projects/{pid}/materials")
def material(pid: str, d: MaterialInput, u=Depends(user)):
    p = get("projects", pid)
    execution(u, p)
    if d.status not in ("Required", "Available", "Shortage"):
        fail(422, "Invalid material status")
    return insert(
        "materials", {"project_id": pid, **d.model_dump(), "recorded_by": u["id"]}
    )


@app.get("/api/projects/{pid}/quality")
def quality(pid: str, u=Depends(user)):
    p = get("projects", pid)
    project_access(u, p)
    if u["role"] == "CUSTOMER":
        return [clean(d) for d in db.quality.find({"project_id": pid, "passed": True})]
    return [clean(d) for d in db.quality.find({"project_id": pid})]


@app.post("/api/projects/{pid}/quality")
def quality_record(pid: str, d: QualityInput, u=Depends(user)):
    p = get("projects", pid)
    execution(u, p)
    return insert(
        "quality", {"project_id": pid, **d.model_dump(), "reviewed_by": u["id"]}
    )


@app.get("/api/admin/summary")
def admin_summary(u=Depends(user)):
    roles(u, "ADMIN")
    users = list(db.users.find())
    req = list(db.requests.find())
    projects = list(db.projects.find())
    qs = list(db.quotes.find())
    payments = list(db.payments.find())
    return {
        "customers": sum(x["role"] == "CUSTOMER" for x in users),
        "managers": sum(x["role"] == "MANAGER" for x in users),
        "workers": sum(x["role"] == "WORKER" for x in users),
        "requests": len(req),
        "projects": len(projects),
        "approved_quotation_cents": sum(
            x["amount_cents"] for x in qs if x["status"] == "Accepted"
        ),
        "verified_receipts_cents": sum(x["amount_cents"] for x in payments),
        "services": {
            name: sum(x["service"] == name for x in req)
            for name in {x["service"] for x in req}
        },
        "project_status": {
            status: sum(x["status"] == status for x in projects)
            for status in ("Active", "Completed")
        },
        "request_months": {
            month: sum(x["created_at"][:7] == month for x in req)
            for month in sorted({x["created_at"][:7] for x in req})
        },
        "workload": {
            x["name"]: sum(
                p.get("manager_id") == x["id"] or x["id"] in p.get("worker_ids", [])
                for p in projects
            )
            for x in users
            if x["role"] in ("WORKER", "MANAGER")
        },
    }


@app.get("/api/admin/customers")
def customers(u=Depends(user)):
    roles(u, "ADMIN")
    return [clean(d) for d in db.users.find({"role": "CUSTOMER"})]


@app.get("/api/admin/enquiries")
def enquiries(u=Depends(user)):
    roles(u, "ADMIN")
    return [clean(d) for d in db.enquiries.find().sort("created_at", -1)]


@app.get("/api/admin/services")
def admin_services(u=Depends(user)):
    roles(u, "ADMIN")
    return [clean(d) for d in db.services.find()]


@app.patch("/api/notifications/{nid}/read")
def read_notification(nid: str, u=Depends(user)):
    if not db.notifications.update_one(
        {"id": nid, "user_id": u["id"]}, {"$set": {"read": True}}
    ).matched_count:
        fail(404, "Notification not found")
    return {"ok": True}


def ensure_shared_message(source, reviewer=None):
    reviewer = reviewer or get("users", source["verified_by"])
    payload = {
        "id": "shared-" + source["id"],
        "created_at": source["verified_at"],
        "project_id": source["project_id"],
        "channel": "customer",
        "sender_id": reviewer["id"],
        "sender_name": reviewer["name"],
        "role": reviewer["role"],
        "text": source.get("share_text", "Verified project progress"),
        "file_id": source["file_id"],
        "source_id": source["id"],
        "verification": "Approved",
    }
    db.messages.update_one(
        {"id": payload["id"]}, {"$setOnInsert": payload}, upsert=True
    )


@app.post("/api/messages/{mid}/share")
def share_approved(mid: str, d: MessageInput, u=Depends(user)):
    source = get("messages", mid)
    execution(u, get("projects", source["project_id"]))
    if source["channel"] != "internal" or source.get("verification") != "Approved":
        fail(409, "Only approved internal evidence can be shared")
    result = db.messages.find_one_and_update(
        {"id": mid, "published": {"$ne": True}},
        {"$set": {"published": True, "share_text": d.text or source["text"]}},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        fail(409, "Already shared")
    ensure_shared_message(result, u)
    audit(u, "approved_progress_shared", mid)
    return {"ok": True}


from fastapi.responses import JSONResponse
from pymongo.errors import ServerSelectionTimeoutError


@app.exception_handler(ServerSelectionTimeoutError)
async def database_unavailable(request: Request, error: ServerSelectionTimeoutError):
    return JSONResponse(
        status_code=503,
        content={
            "detail": "MongoDB is unavailable. Start your local MongoDB service and check backend/.env."
        },
    )


@app.post("/api/requests/{rid}/reply")
def request_reply(rid: str, d: RequestReply, u=Depends(user)):
    roles(u, "CUSTOMER")
    r = get("requests", rid)
    request_access(u, r)
    owned_files(u, d.file_ids, "image")
    result = db.requests.update_one(
        {"id": rid, "status": "More Information Required"},
        {
            "$set": {"status": "Under Review"},
            "$push": {
                "history": {
                    "status": "Customer Response",
                    "note": d.text,
                    "date": now(),
                    "by": u["id"],
                }
            },
            "$addToSet": {"file_ids": {"$each": d.file_ids}},
        },
    )
    if not result.modified_count:
        fail(409, "A reply is allowed only when Admin requests more information")
    for a in db.users.find({"role": "ADMIN"}):
        notify(a["id"], "Customer provided additional request information")
    audit(u, "request_reply", rid)
    return {"ok": True}


@app.put("/api/quotes/{qid}")
def edit_draft(qid: str, d: QuoteInput, u=Depends(user)):
    roles(u, "ADMIN")
    q = get("quotes", qid)
    if q["status"] != "Draft" or d.phase != q["phase"]:
        fail(409, "Only an unpublished draft can be edited; retain its phase")
    if d.pdf_id != q["pdf_id"]:
        owned_files(u, [d.pdf_id], "pdf")
    payload = {
        "title": d.title,
        "description": d.description,
        "duration": d.duration,
        "terms": d.terms,
        "pdf_id": d.pdf_id,
        "amount_cents": quotation_total(d),
        "tax_percent": str(d.tax_percent),
        "discount_cents": cents(d.discount),
        "items": [
            {
                "description": i.description,
                "category": i.category,
                "quantity": str(i.quantity),
                "unit": i.unit,
                "unit_price_cents": cents(i.unit_price),
                "total_cents": cents(i.quantity * i.unit_price),
            }
            for i in d.items
        ],
        "updated_at": now(),
    }
    if not db.quotes.update_one(
        {"id": qid, "status": "Draft"}, {"$set": payload}
    ).matched_count:
        fail(409, "Quotation was already published")
    audit(u, "quote_draft_edited", qid)
    return clean(get("quotes", qid))


from .models import EmployeeDetails


@app.patch("/api/users/{uid}")
def employee_details(uid: str, d: EmployeeDetails, u=Depends(user)):
    roles(u, "ADMIN")
    target = get("users", uid)
    if target["role"] not in ("MANAGER", "WORKER"):
        fail(403, "This endpoint edits employee details only")
    try:
        db.users.update_one(
            {"id": uid}, {"$set": {**d.model_dump(), "email": d.email.lower()}}
        )
    except DuplicateKeyError:
        fail(409, "Email already registered")
    audit(u, "employee_edited", uid)
    return clean(get("users", uid))


@app.put("/api/tasks/{tid}")
def edit_task(tid: str, d: TaskInput, u=Depends(user)):
    t = get("tasks", tid)
    p = get("projects", t["project_id"])
    execution(u, p)
    valid_date(d.deadline)
    if d.worker_id not in p["worker_ids"]:
        fail(422, "Select a worker assigned to this project")
    db.tasks.update_one({"id": tid}, {"$set": {**d.model_dump(), "updated_at": now()}})
    notify(d.worker_id, "Task updated: " + d.title)
    audit(u, "task_reassigned_or_edited", tid)
    return {"ok": True}


@app.put("/api/milestones/{mid}")
def edit_milestone(mid: str, d: MilestoneInput, u=Depends(user)):
    m = get("milestones", mid)
    p = get("projects", m["project_id"])
    execution(u, p)
    valid_date(d.deadline)
    if d.phase not in [ph["number"] for ph in p["phases"]]:
        fail(422, "Phase not found")
    db.milestones.update_one(
        {"id": mid},
        {"$set": {**d.model_dump(), "updated_at": now(), "updated_by": u["id"]}},
    )
    audit(u, "milestone_definition_updated", mid)
    return {"ok": True}
