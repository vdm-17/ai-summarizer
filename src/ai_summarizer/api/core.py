"""API core."""

import logging
from pathlib import Path

from ai_summarizer.api.errors import (
    OutputFileAlreadyExistsError,
    SummarySavingError,
)
from ai_summarizer.api.models import Summary
from ai_summarizer.api.pipeline import summarize_source
from ai_summarizer.api.settings import (
    Detail,
    LLMAPISettings,
    OCRSettings,
    Quality,
    SummarizingAgentSettings,
    SummarizingSettings,
    SummaryType,
    TranslatingAgentSettings,
)

logger = logging.getLogger(__name__)


class AISummarizer:
    """AI summarizer."""

    def __init__(
        self,
        *,
        ocr_settings: OCRSettings,
        llm_api_settings: LLMAPISettings,
        summarizing_agent_settings: SummarizingAgentSettings,
        translating_agent_settings: TranslatingAgentSettings,
        structurizing_min_tokens: int,
    ) -> None:
        self._ocr_settings = ocr_settings
        self._llm_api_settings = llm_api_settings
        self._summarizing_agent_settings = summarizing_agent_settings
        self._translating_agent_settings = translating_agent_settings
        self._structurizing_min_tokens = structurizing_min_tokens

    def summarize_source(
        self,
        filename: str | Path,
        *,
        summary_type: SummaryType = SummaryType.arbitrary_text,
        detail: Detail = Detail.medium,
        quality: Quality = Quality.medium,
        lang: str = "eng",
        structurize: bool = True,
        show_progress: bool = False,
    ) -> Summary:
        """Summarizes source content."""

        settings = SummarizingSettings(
            ocr=self._ocr_settings,
            llm_api=self._llm_api_settings,
            summarizing_agent=self._summarizing_agent_settings,
            translating_agent=self._translating_agent_settings,
            summary_type=summary_type,
            detail=detail,
            quality=quality,
            lang=lang,
            structurize=structurize,
            structurizing_min_tokens=self._structurizing_min_tokens,
        )

        summary = summarize_source(
            filename, settings, show_progress=show_progress
        )

        return summary

    def write_source_summary(
        self,
        filename: str | Path,
        *,
        output_dir: str | Path | None = None,
        summary_type: SummaryType = SummaryType.arbitrary_text,
        detail: Detail = Detail.medium,
        quality: Quality = Quality.medium,
        lang: str = "eng",
        structurize: bool = True,
        overwrite: bool = True,
        show_progress: bool = False,
    ) -> None:
        """Summarizes source content and writes summary into file."""

        filename = Path(filename)
        if not output_dir:
            output_dir = filename.parent

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        source_name = filename.name.removesuffix(filename.suffix)
        output_filename = output_dir / f"{source_name}-summary.md"

        if not overwrite and output_filename.exists():
            raise OutputFileAlreadyExistsError

        summary = self.summarize_source(
            filename,
            summary_type=summary_type,
            detail=detail,
            quality=quality,
            lang=lang,
            structurize=structurize,
            show_progress=show_progress,
        )

        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(summary.md_text)
        except OSError as e:
            raise SummarySavingError from e

        summary_saving_message = (
            "Summary of source content successfully writen at "
            f"{output_filename}"
        )

        logger.debug(summary_saving_message)

        if show_progress:
            print()
            print(summary_saving_message)
