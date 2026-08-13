"""Errors of summarizer API internal services."""

from ..errors import ApplicationError


class InternalServiceError(ApplicationError):
    """Internal service error."""
