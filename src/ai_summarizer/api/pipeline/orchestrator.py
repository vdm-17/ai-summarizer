"""The orchestrator of the summarizing pipeline."""

import logging
from pathlib import Path

from ai_summarizer.api.models import Summary
from ai_summarizer.api.settings import SummarizingSettings

from .extracting import extract_content
from .structurizing import structurize_content
from .summarizing import summarize_content

logger = logging.getLogger(__name__)


def summarize_source(
    filename: str | Path,
    settings: SummarizingSettings,
    *,
    show_progress: bool = False,
) -> Summary:
    """Summarizes source content."""

    logger.debug("Summarizing source content.")

    content = extract_content(
        filename,
        settings,
        show_progress=show_progress,
    )

    if settings.structurize:
        content = structurize_content(content, settings)

    summary = summarize_content(
        content,
        settings,
        show_progress=show_progress,
    )

    logger.info("Source content summarized successfully.")

    return summary
