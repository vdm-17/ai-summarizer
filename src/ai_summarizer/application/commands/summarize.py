"""Summarize command."""

import os
from pathlib import Path

from ai_summarizer.api.core import AISummarizer
from ai_summarizer.api.settings import (
    Detail,
    LLMAPISettings,
    OCRSettings,
    Quality,
    SummarizingAgentSettings,
    SummaryType,
    TranslatingAgentSettings,
)
from ai_summarizer.application.commands.base import command
from ai_summarizer.application.definitions import AppEnvVar
from ai_summarizer.application.services.authenticator import get_credentials
from ai_summarizer.application.services.configurator import load_config


@command()
def summarize(
    filename: Path,
    *,
    output_dir: Path | None = None,
    summary_type: SummaryType = SummaryType.arbitrary_text,
    detail: Detail = Detail.medium,
    quality: Quality = Quality.medium,
    lang: str = "eng",
    structurize: bool = True,
    overwrite: bool = False,
    show_progress: bool = True,
) -> None:
    """Summarizes source content."""

    llm_api_key = get_credentials()
    config = load_config()

    summarizer = AISummarizer(
        ocr_settings=OCRSettings(
            quality=config.ocr.quality,
            langs=config.ocr.langs,
        ),
        llm_api_settings=LLMAPISettings(
            base_url=config.general.llm_api_base_url,
            api_key=llm_api_key,
        ),
        summarizing_agent_settings=SummarizingAgentSettings(
            context_size=config.summarizing_agent.context_size,
            model=config.summarizing_agent.model,
            max_input_tokens=config.summarizing_agent.max_input_tokens,
            max_output_tokens=config.summarizing_agent.max_output_tokens,
        ),
        translating_agent_settings=TranslatingAgentSettings(
            model=config.translating_agent.model
        ),
        structurizing_min_tokens=config.general.structurizing_min_tokens,
    )

    env_output_dirname = os.getenv(AppEnvVar.output_dir)

    summarizer.write_source_summary(
        filename,
        output_dir=(output_dir or env_output_dirname),
        summary_type=summary_type,
        detail=detail,
        quality=quality,
        lang=lang,
        structurize=structurize,
        overwrite=overwrite,
        show_progress=show_progress,
    )
