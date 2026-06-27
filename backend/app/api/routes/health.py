from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from core.database import engine
from core.logging import log_event, logger

h_router = APIRouter(prefix="/health")


async def _check_redis(request: Request) -> bool:
    redis_service = getattr(request.app.state, "redis_service", None)
    if redis_service is None:
        log_event(
            event="health.redis.ping.skipped",
            message="Redis service not available on app state",
            path="/health/",
        )
        return False
    try:
        await redis_service.redis_client.ping()
        return True
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
        return False


async def _check_database(request: Request) -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception(
            "Database health check failed",
            extra={
                "event": "health.database.ping.failed",
                "method": request.method,
                "path": request.url.path,
                "status_code": 503,
                "error_code": "SERVICE_UNAVAILABLE",
            },
        )
        return False


@h_router.get(
    "/",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"health": True, "redis": True, "database": True}
                }
            }
        },
        503: {
            "content": {
                "application/json": {
                    "example": {"health": False, "redis": False, "database": False}
                }
            }
        },
    },
)
async def root(request: Request):
    redis_ok = await _check_redis(request)
    db_ok = await _check_database(request)
    healthy = redis_ok and db_ok

    body = {"health": healthy, "redis": redis_ok, "database": db_ok}
    log_event(
        event="health.check.run.succeeded",
        message="Health check completed",
        path="/health/",
        redis_ok=redis_ok,
        database_ok=db_ok,
        status_code=200 if healthy else 503,
    )

    if not healthy:
        return JSONResponse(status_code=503, content=body)

    return body
