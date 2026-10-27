"""The HTTP interface: POST /ask streams typed server-sent events, Stop cancels the upstream call, reviewers answer paused runs.

This module deliberately has no `from __future__ import annotations`: FastAPI reads the annotations of the handlers
defined inside `create_app` to resolve their dependencies.
"""

import json
import logging
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from streaming_assistant.application.assistant import Assistant, Event, UnauthorizedError
from streaming_assistant.application.ports import AuditLog, Authenticator
from streaming_assistant.application.review import ReviewDesk
from streaming_assistant.domain.audit import verify
from streaming_assistant.domain.errors import ReviewRejectedError, UnknownRunError
from streaming_assistant.infrastructure.catalog import PageCatalog

LOGGER = logging.getLogger("streaming_assistant.http")
STATIC = Path(__file__).parent / "static"
SSE_HEADERS = {"Cache-Control": "no-store", "X-Accel-Buffering": "no", "Connection": "keep-alive"}


class AskIn(BaseModel):
    """A customer question."""

    question: str = Field(min_length=3, max_length=1000)


class ReviewIn(BaseModel):
    """A reviewer's answer to a paused run."""

    reviewer_id: str = Field(min_length=1, max_length=64)
    answer: str = Field(max_length=2000)
    cited: list[str] = Field(default_factory=list, max_length=5)
    no_page: bool = False


def encode(event: Event) -> str:
    """One server-sent event."""
    return f"event: {event.name}\ndata: {json.dumps(event.data)}\n\n"


def create_app(
    assistant: Assistant, desk: ReviewDesk, catalog: PageCatalog, authenticator: Authenticator, audit: AuditLog
) -> FastAPI:
    """Build the app over the assistant and its collaborators."""
    app = FastAPI(title="Streaming support assistant", version="0.1.0")

    def role(authorization: Annotated[str | None, Header()] = None) -> str:
        found = authenticator.role_of((authorization or "").removeprefix("Bearer ").strip())
        if found is None:
            raise HTTPException(status_code=401, detail="sign in first")
        return found

    def reviewer(found: Annotated[str, Depends(role)]) -> None:
        if found != "reviewer":
            raise HTTPException(status_code=403, detail="reviewers only")

    async def sse(events: AsyncIterator[Event]) -> AsyncIterator[str]:
        async for event in events:
            yield encode(event)

    @app.get("/", response_class=HTMLResponse)
    def home() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/review", response_class=HTMLResponse)
    def review_page() -> FileResponse:
        return FileResponse(STATIC / "review.html")

    @app.post("/ask")
    async def ask(body: AskIn, authorization: Annotated[str | None, Header()] = None) -> StreamingResponse:
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        try:
            prepared = await assistant.prepare(
                run_id, body.question, (authorization or "").removeprefix("Bearer ").strip()
            )
        except UnauthorizedError:
            raise HTTPException(status_code=401, detail="sign in first") from None
        LOGGER.info("run started", extra={"fields": {"run_id": run_id, "route": prepared.route.kind}})
        return StreamingResponse(
            sse(assistant.stream(prepared)), media_type="text/event-stream", headers={**SSE_HEADERS, "X-Run-Id": run_id}
        )

    @app.post("/runs/{run_id}/stop", status_code=202)
    def stop(run_id: str, _: Annotated[str, Depends(role)]) -> dict[str, str]:
        assistant.stops.request(run_id)
        return {"run_id": run_id, "status": "stop requested"}

    @app.get("/runs/{run_id}/status")
    def status(run_id: str, _: Annotated[str, Depends(role)]) -> dict[str, str | None]:
        try:
            return {"run_id": run_id, "status": desk.status(run_id)}
        except UnknownRunError:
            raise HTTPException(status_code=404, detail="no such run") from None

    @app.get("/runs/{run_id}/resume")
    async def resume(run_id: str, _: Annotated[str, Depends(role)]) -> StreamingResponse:
        try:
            events = assistant.resume(run_id)
            first = await events.__anext__()
        except UnknownRunError as error:
            raise HTTPException(status_code=409, detail=str(error)) from None

        async def chained() -> AsyncIterator[Event]:
            yield first
            async for event in events:
                yield event

        return StreamingResponse(sse(chained()), media_type="text/event-stream", headers=SSE_HEADERS)

    @app.get("/reviews", dependencies=[Depends(reviewer)])
    def waiting() -> list[dict[str, object]]:
        return [
            {"run_id": r.run_id, "question": r.question, "reason": r.reason, "retrieved": list(r.retrieved)}
            for r in desk.waiting()
        ]

    @app.post("/reviews/{run_id}/answer", dependencies=[Depends(reviewer)])
    def answer(run_id: str, body: ReviewIn) -> JSONResponse:
        try:
            run = desk.answer(run_id, body.reviewer_id, body.answer, body.cited, body.no_page)
        except UnknownRunError:
            raise HTTPException(status_code=404, detail="no such run") from None
        except ReviewRejectedError as error:
            raise HTTPException(status_code=422, detail=str(error)) from None
        return JSONResponse({"run_id": run.run_id, "status": run.status})

    @app.get("/audit/verify", dependencies=[Depends(reviewer)])
    def audit_verify() -> dict[str, object]:
        entries = audit.entries()
        return {"entries": len(entries), "first_broken_index": verify(entries)}

    @app.get("/pages/{page_id}", response_class=HTMLResponse)
    def page(page_id: str) -> HTMLResponse:
        found = catalog.page_html(page_id)
        if found is None:
            raise HTTPException(status_code=404, detail="no such page")
        return HTMLResponse(found)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> dict[str, object]:
        return {"status": "ready", "sections": len(catalog.sections)}

    @app.get("/stats")
    def stats() -> dict[str, int]:
        return dict(assistant.stats)

    return app
