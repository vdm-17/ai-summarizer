"""AI summarizer errors."""

from inspect import cleandoc


class AISummarizerError(Exception):
    """
    AI summarizer error.

    Provides default error message based on the inherited
    error docstring if no message is received.
    """

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = cleandoc(self.__doc__ or "")

        super().__init__(message)
