"""Custom exception hierarchy and FastAPI exception handlers.

Every handler maps internal failures to the shared `Error` response shape
(FR-021): a clear, specific, user-facing message that never exposes stack
traces, credentials, infrastructure hostnames, or raw third-party error
payloads. Application code should raise one of the AppError subclasses
below rather than a bare HTTPException, so every error path is consistent.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.models.schemas import Error

logger = logging.getLogger("rag_document_qa")


class AppError(Exception):
    status_code = 500
    default_detail = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class ValidationAppError(AppError):
    status_code = 422
    default_detail = "The request could not be validated."


class BadRequestError(AppError):
    """The request is well-formed but its content is unacceptable (e.g. an
    empty, corrupted, password-protected, oversized, or unsupported-format
    file upload) -- distinct from ValidationAppError's 422 schema failures."""

    status_code = 400
    default_detail = "The request could not be processed."


class UnauthorizedError(AppError):
    status_code = 401
    default_detail = "Invalid credentials."


class ForbiddenError(AppError):
    status_code = 403
    default_detail = "You are not authorized to perform this action."


class NotFoundError(AppError):
    status_code = 404
    default_detail = "The requested resource was not found."


class ConflictError(AppError):
    status_code = 409
    default_detail = "The request conflicts with existing data."


class RateLimitExceededError(AppError):
    status_code = 429
    default_detail = "Rate limit exceeded."


class UpstreamServiceError(AppError):
    """A retrieval or generation dependency failed (FR-021)."""

    status_code = 502
    default_detail = "The request could not be completed. Please try again."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.exception("Unhandled application error", exc_info=exc)
        return JSONResponse(
            status_code=exc.status_code, content=Error(detail=exc.detail).model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=Error(
                detail="The request was malformed or missing required fields."
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=Error(detail="An unexpected error occurred. Please try again.").model_dump(),
        )
