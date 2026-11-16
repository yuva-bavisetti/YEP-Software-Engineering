"""A renewable MongoDB lease serializes local business writes across API processes.
Standalone MongoDB compatible. A crashed process loses its lease after 30 seconds.
Source records remain authoritative and reconciliation repairs derived views.
"""

import asyncio, secrets
from contextlib import suppress
from datetime import datetime, timezone, timedelta
from fastapi.responses import JSONResponse
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError
from starlette.concurrency import run_in_threadpool


def install(app, ctx):
    @app.middleware("http")
    async def serialize(request, call_next):
        if (
            request.method not in ("POST", "PUT", "PATCH", "DELETE")
            or not request.url.path.startswith("/api/")
            or "/auth/" in request.url.path
            or not request.cookies.get("yep_session")
        ):
            return await call_next(request)
        token = secrets.token_hex(24)

        def acquire():
            now = datetime.now(timezone.utc)
            return ctx.db.workflow_locks.find_one_and_update(
                {"_id": "business", "expires": {"$lte": now}},
                {"$set": {"owner": token, "expires": now + timedelta(seconds=30)}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )

        try:
            await run_in_threadpool(acquire)
        except DuplicateKeyError:
            return JSONResponse(
                status_code=409,
                content={
                    "detail": "Another business update is in progress. Retry after it finishes."
                },
                headers={"Retry-After": "1"},
            )
        except PyMongoError:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "MongoDB is unavailable. Check your local database service."
                },
            )

        async def renew():
            while True:
                await asyncio.sleep(5)
                await run_in_threadpool(
                    lambda: ctx.db.workflow_locks.update_one(
                        {"_id": "business", "owner": token},
                        {
                            "$set": {
                                "expires": datetime.now(timezone.utc)
                                + timedelta(seconds=30)
                            }
                        },
                    )
                )

        heartbeat = asyncio.create_task(renew())
        try:
            response = await call_next(request)
            if response.status_code < 400:
                await run_in_threadpool(ctx.recover, ctx.db)
            return response
        finally:
            heartbeat.cancel()
            with suppress(asyncio.CancelledError, PyMongoError):
                await heartbeat
            with suppress(PyMongoError):
                await run_in_threadpool(
                    lambda: ctx.db.workflow_locks.delete_one(
                        {"_id": "business", "owner": token}
                    )
                )
