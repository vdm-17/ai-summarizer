"""Content extracting."""

from .errors import ContentExtractingError
from .extracting import extract_content

__all__ = ["extract_content", "ContentExtractingError"]
