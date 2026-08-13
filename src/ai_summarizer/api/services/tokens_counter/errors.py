"""Errors of the content tokens counter."""

from ..errors import InternalServiceError


class ContentTokensCounterError(InternalServiceError):
    """Content tokens counter error."""


class TokensCountingError(ContentTokensCounterError):
    """Error: unable to count tokens in the given content."""
