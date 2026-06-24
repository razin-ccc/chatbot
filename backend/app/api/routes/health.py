from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.logging import logger

h_router = APIRouter(prefix="/health")


@h_router.get(
    "/",
    responses={
        200: {"content": {"application/json": {"example": {"health": True, "redis": True}}}},
        503: {"content": {"application/json": {"example": {"health": False, "redis": False}}}},
    },
)
async def root(request: Request):
    logger.info("GET /health/ endpoint was hit")

    redis_service = getattr(request.app.state, "redis_service", None)
    redis_ok = False

    if redis_service is not None:
        try:
            await redis_service.redis_client.ping()
            redis_ok = True
        except Exception:
            logger.exception("Redis health check failed")

    body = {"health": redis_ok, "redis": redis_ok}

    if not redis_ok:
        return JSONResponse(status_code=503, content=body)

    return body
