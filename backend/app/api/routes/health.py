from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.logging import log_event, logger

h_router = APIRouter(prefix="/health")


@h_router.get(
    "/",
    responses={
        200: {"content": {"application/json": {"example": {"health": True, "redis": True}}}},
        503: {"content": {"application/json": {"example": {"health": False, "redis": False}}}},
    },
)
async def root(request: Request):
    redis_service = getattr(request.app.state, "redis_service", None)
    redis_ok = False

    if redis_service is not None:
        try:
            await redis_service.redis_client.ping()
            redis_ok = True
        except Exception:
            logger.exception(
                "Redis health check failed",
                extra={
                    "event": "health.redis.ping.failed",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 503,
                    "error_code": "SERVICE_UNAVAILABLE",
                },
            )
    else:
        log_event(
            event="health.redis.ping.skipped",
            message="Redis service not available on app state",
            path="/health/",
        )

    body = {"health": redis_ok, "redis": redis_ok}
    log_event(
        event="health.check.run.succeeded",
        message="Health check completed",
        path="/health/",
        redis_ok=redis_ok,
        status_code=200 if redis_ok else 503,
    )

    if not redis_ok:
        return JSONResponse(status_code=503, content=body)

    return body
