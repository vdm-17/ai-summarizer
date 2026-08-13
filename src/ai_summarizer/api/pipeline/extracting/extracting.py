"""Content extracting."""

import logging
from pathlib import Path

from ai_summarizer.api import models
from ai_summarizer.api.settings import Quality, SummarizingSettings

from .errors import (
    InputFileNotExistsError,
    InputFileNotSpecifiedError,
    InputFileUnsupportedExtensionError,
    InputPathIsDirectoryError,
)

logger = logging.getLogger(__name__)


def extract_content(
    filename: str | Path,
    settings: SummarizingSettings,
    *,
    show_progress: bool = False,
) -> models.UnstructuredContent:
    """Extracts content from file."""

    logger.debug("Extracting source content.")

    if show_progress:
        print("The application extracts content from the source file.")
        print("Please wait while the content is being extracted...")
        print()

    if isinstance(filename, str):
        filename = Path(filename)

    if not filename.name:
        raise InputFileNotSpecifiedError()
    if not filename.exists():
        raise InputFileNotExistsError()
    if filename.is_dir():
        raise InputPathIsDirectoryError()

    file_extension = filename.suffix[1:].lower()

    match settings.quality:
        case Quality.low:
            image_detail = "low"
        case Quality.medium:
            image_detail = "auto"
        case Quality.high:
            image_detail = "high"
        case Quality.max:
            image_detail = "original"

    match file_extension:
        case "md" | "markdown":
            from ai_summarizer.api.pipeline.extracting.md import (
                extract_content_from_md,
            )

            content = extract_content_from_md(
                filename, image_detail=image_detail
            )
        case "pdf":
            from ai_summarizer.api.pipeline.extracting.pdf import (
                extract_content_from_pdf,
            )

            content = extract_content_from_pdf(
                filename,
                image_detail=image_detail,
                ocr_settings=settings.ocr,
                show_progress=show_progress,
            )
        case _:
            logger.error(
                "Content extraction error: given file "
                f"with unsupported extension - {file_extension}."
            )
            raise InputFileUnsupportedExtensionError(file_extension)

    logger.debug("Source content extracted successfully.")
    return content
