"""API errors."""

from ai_summarizer.errors import AISummarizerError


class APIError(AISummarizerError):
    """API error."""


class OutputFileAlreadyExistsError(AISummarizerError):
    """
    Error: output file is already exists.

    Set overwrite=True to suppress error.
    """


class SummarySavingError(AISummarizerError):
    """Error: unable to save summary into file."""
