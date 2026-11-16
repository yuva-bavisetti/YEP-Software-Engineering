"""Actual backend process restart check. Opt in with MONGO_TEST_URL.
Uses a fresh database and upload directory; never touches the demo database.
"""

import os, sys, time, socket, subprocess, uuid
from pathlib import Path
import pytest, httpx, bcrypt
from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.mark.skipif(
    not os.getenv("MONGO_TEST_URL"),
    reason="Requires a real MongoDB server; set MONGO_TEST_URL",
)
def test_records_sessions_and_files_survive_backend_restart(tmp_path):
    mongo = MongoClient(os.environ["MONGO_TEST_URL"], serverSelectionTimeoutMS=3000)
    dbname = "yep_test_restart_" + uuid.uuid4().hex
    database = mongo[dbname]
    database.users.insert_one(
        {
            "id": "admin-restart",
            "name": "Admin",
            "email": "owner@yep.local",
            "role": "ADMIN",
            "active": True,
            "password": bcrypt.hashpw(b"Demo@12345", bcrypt.gensalt()).decode(),
        }
    )
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {
        **os.environ,
        "MONGO_URL": os.environ["MONGO_TEST_URL"],
        "MONGO_DB": dbname,
        "UPLOAD_DIR": str(tmp_path / "uploads"),
    }

    def launch():
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--port",
                str(port),
                "--host",
                "127.0.0.1",
            ],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        for _ in range(100):
            if proc.poll() is not None:
                raise RuntimeError(proc.stderr.read().decode())
            try:
                if httpx.get(f"http://127.0.0.1:{port}/api/health").status_code == 200:
                    return proc
            except httpx.TransportError:
                pass
            time.sleep(0.1)
        proc.terminate()
        raise RuntimeError("Server did not become ready")

    proc = None
    try:
        proc = launch()
        c = httpx.Client(base_url=f"http://127.0.0.1:{port}")
        assert (
            c.post(
                "/api/auth/login",
                json={"email": "owner@yep.local", "password": "Demo@12345"},
            ).status_code
            == 200
        )
        from app.demo_assets import quotation_pdf

        data = quotation_pdf()
        file = c.post(
            "/api/files", files={"file": ("quotation.pdf", data, "application/pdf")}
        ).json()
        # Persistent business records are inserted here; full API workflow is covered separately against this same real engine.
        database.projects.insert_one(
            {
                "id": "project-restart",
                "customer_id": "customer-restart",
                "request_id": "request-restart",
                "initial_quote_id": "quote-restart",
                "title": "Restart proof",
                "phases": [],
                "worker_ids": [],
                "channels": ["internal", "customer"],
                "status": "Active",
                "progress": 0,
            }
        )
        database.quotes.insert_one(
            {
                "id": "quote-restart",
                "request_id": "request-restart",
                "project_id": "project-restart",
                "customer_id": "customer-restart",
                "phase": 1,
                "revision": 1,
                "status": "Accepted",
                "amount_cents": 500000,
                "pdf_id": file["id"],
            }
        )
        database.payments.insert_one(
            {
                "id": "payment-restart",
                "project_id": "project-restart",
                "amount_cents": 100000,
                "idempotency_key": "restart-proof",
            }
        )
        database.messages.insert_one(
            {
                "id": "message-restart",
                "project_id": "project-restart",
                "channel": "customer",
                "text": "Persistent conversation",
                "created_at": "2026-11-16T00:00:00+00:00",
            }
        )
        proc.terminate()
        proc.wait(timeout=10)
        proc = launch()
        assert c.get("/api/auth/me").status_code == 200
        assert c.get("/api/files/" + file["id"]).content == data
        assert (
            c.get("/api/projects/project-restart/finance").json()["balance_cents"]
            == 400000
        )
        assert (
            c.get("/api/projects/project-restart/chat/customer").json()[0]["text"]
            == "Persistent conversation"
        )
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)
        mongo.drop_database(dbname)
