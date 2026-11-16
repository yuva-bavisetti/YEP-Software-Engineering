"""Backend authorization policies, shared by every protected workflow."""

from fastapi import HTTPException


def fail(code, message):
    raise HTTPException(code, message)


def roles(u, *allowed):
    if u["role"] not in allowed:
        fail(403, "Permission denied")


def project_access(u, p):
    if (
        u["role"] == "ADMIN"
        or (u["role"] == "CUSTOMER" and p["customer_id"] == u["id"])
        or (u["role"] == "MANAGER" and p.get("manager_id") == u["id"])
        or (u["role"] == "WORKER" and u["id"] in p.get("worker_ids", []))
    ):
        return
    fail(403, "Project is not assigned to you")


def execution(u, p):
    roles(u, "ADMIN", "MANAGER")
    project_access(u, p)
    if p["status"] == "Completed":
        fail(409, "Completed projects are read-only")


def financial(u, customer):
    roles(u, "ADMIN", "CUSTOMER")
    if u["role"] == "CUSTOMER" and customer != u["id"]:
        fail(403, "Private customer record")


def request_access(u, r):
    financial(u, r["customer_id"])


def channel_access(u, p, channel):
    project_access(u, p)
    if channel not in ("internal", "customer"):
        fail(422, "Invalid channel")
    if (channel == "internal" and u["role"] == "CUSTOMER") or (
        channel == "customer" and u["role"] == "WORKER"
    ):
        fail(403, "This chat is private")
