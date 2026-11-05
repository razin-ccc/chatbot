import logging
from time import perf_counter
from uuid import uuid7

from fastapi import Request

from core.client_info import client_ip_for_logging, client_user_agent
from core.config import API_PREFIX
from core.logging import clear_request_context, log_event, set_request_context
from services.audit import AuditEntry


def _record_audit_entry(request: Request, status_code: int, duration_ms: float) -> None:
    """
    Queue an audit row for an API request.

    Pages, assets and health checks are skipped. Query strings and bodies are left out,
    as they may hold private data.
    """
    if request.method == "OPTIONS" or not request.url.path.startswith(f"{API_PREFIX}/"):
        return
    writer = getattr(request.app.state, "audit_writer", None)
    if writer is None:
        return
    writer.record(
        AuditEntry(
            user_id=getattr(request.state, "user_id", None),
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=round(duration_ms),
            ip_address=client_ip_for_logging(request),
            user_agent=client_user_agent(request),
            request_id=request.state.request_id[:64],
        )
    )


async def request_logging_middleware(request: Request, call_next):
    """Give each request an ID, write its operational log line, and queue its audit row."""
    request_id = request.headers.get("X-Request-ID") or str(uuid7())
    request.state.request_id = request_id
    set_request_context(request_id=request_id)
    start_time = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((perf_counter() - start_time) * 1000, 2)
        log_event(
            event="http.request.process.failed",
            message="HTTP request failed before response generation",
            level=logging.ERROR,
            method=request.method,
            path=request.url.path,
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
            duration_ms=duration_ms,
        )
        _record_audit_entry(request, 500, duration_ms)
        clear_request_context()
        raise

    duration_ms = round((perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    log_event(
        event="http.request.process.succeeded",
        message="HTTP request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    _record_audit_entry(request, response.status_code, duration_ms)
    clear_request_context()
    return response
