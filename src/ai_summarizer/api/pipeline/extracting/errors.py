"""Content extracting errors."""

from ..errors import SummarizingPipelineError


class ContentExtractingError(SummarizingPipelineError):
    """Error: unable to extract content from the given file."""


class InputFileNotSpecifiedError(ContentExtractingError):
    """Error: not specified input file."""


class InputFileNotExistsError(ContentExtractingError):
    """Error: input file does not exist."""


class InputPathIsDirectoryError(ContentExtractingError):
    """Error: given input path is a directory."""


class InputFileUnsupportedExtensionError(ContentExtractingError):
    """Error: unsupported extension of input file."""

    def __init__(self, extension: str) -> None:
        message = f"Error: {extension} is invalid extension of input file."
        super().__init__(message)
