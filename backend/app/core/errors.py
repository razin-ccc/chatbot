import logging

from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from core.logging import log_event, logger


class UserBaseException(HTTPException):
    code = "Application_Error"


class BadRequest(UserBaseException):
    code = "BAD_REQUEST"

    def __init__(self, message: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


class UnauthorizedError(UserBaseException):
    code = "UNAUTHORIZED"

    def __init__(self, message: str = "Not Authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(UserBaseException):
    code = "FORBIDDEN"

    def __init__(self, message: str = "Not Authorized to perform operation"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)


class NotFoundError(UserBaseException):
    code = "NOT_FOUND"

    def __init__(self, message: str = "Not Found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class ValidationError(UserBaseException):
    code = "UNPROCESSABLE_ENTITY"

    def __init__(self, message: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
        )


class ConflictError(UserBaseException):
    code = "CONFLICT"

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )


class TooManyRequestsError(UserBaseException):
    code = "TOO_MANY_REQUESTS"

    def __init__(self, message: str = "Too many requests"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
        )


class UnknownError(UserBaseException):
    code = "INTERNAL_SERVER_ERROR"

    def __init__(self, message: str = "Internal Server Error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )


class ServiceUnavailableError(UserBaseException):
    code = "SERVICE_UNAVAILABLE"

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
        )


ERROR_EVENT_BY_CODE = {
    "BAD_REQUEST": "api.request.bad.failed",
    "UNAUTHORIZED": "api.auth.authenticate.failed",
    "FORBIDDEN": "api.auth.authorize.failed",
    "NOT_FOUND": "api.resource.lookup.failed",
    "UNPROCESSABLE_ENTITY": "api.request.validate.failed",
    "CONFLICT": "api.request.conflict.failed",
    "TOO_MANY_REQUESTS": "api.request.rate_limit.failed",
    "SERVICE_UNAVAILABLE": "api.service.availability.failed",
    "INTERNAL_SERVER_ERROR": "api.request.process.failed",
}


def _error_event(exc: UserBaseException) -> str:
    return ERROR_EVENT_BY_CODE.get(exc.code, "api.request.process.failed")


def _error_level(status_code: int) -> int:
    return logging.WARNING if status_code < 500 else logging.ERROR


async def application_exception_handler(
    request: Request,
    exc: UserBaseException,
):
    log_event(
        event=_error_event(exc),
        message="Application exception handled",
        level=_error_level(exc.status_code),
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        error_code=exc.code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.detail,
            },
        },
    )


async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unhandled exception on %s",
        request.url.path,
        extra={
            "event": "api.request.process.failed",
            "method": request.method,
            "path": request.url.path,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal Server Error",
            },
        },
    )
