from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from core.logging import logger


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


async def application_exception_handler(
    request: Request,
    exc: UserBaseException,
):
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
    logger.exception(f"Unhandled exception on {request.url.path}")

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
