"""Content summarizing."""

import logging
from typing import overload

from tqdm import tqdm

from ai_summarizer.api import models
from ai_summarizer.api.services.agents import (
    SummarizingAgent,
    TranslatingAgent,
)
from ai_summarizer.api.services.agents.summarizing import (
    ArbitraryTextOutput,
    QuestionsListOutput,
)
from ai_summarizer.api.settings import SummarizingSettings

logger = logging.getLogger(__name__)


def _summarize_unstructured_content(
    content: models.UnstructuredContent,
    summarizing_agent: SummarizingAgent,
    *,
    show_progress: bool,
) -> models.UnstructuredSummary:
    """Summarizes unstructured content."""

    agent_response = summarizing_agent.get_output(
        content,
        show_progress=show_progress,
    )

    match agent_response:
        case ArbitraryTextOutput():
            summary = models.ArbitraryTextSummary(agent_response.text)
        case QuestionsListOutput():
            summary_items = [
                models.QuestionsListSummaryItem(
                    question=i.question,
                    answer=i.answer,
                    answer_source_pages=i.answer_source_pages,
                    answer_source_fragment=i.answer_source_fragment,
                )
                for i in agent_response.items
            ]
            summary = models.QuestionsListSummary(items=summary_items)

    return models.UnstructuredSummary(summary)


@overload
def _summarize_structured_content(
    topic: models.StructuredContent,
    summarizing_agent: SummarizingAgent,
    translating_agent: TranslatingAgent,
    *,
    show_progress: bool,
) -> models.StructuredSummary: ...
@overload
def _summarize_structured_content(
    topic: models.ContentTopic,
    summarizing_agent: SummarizingAgent,
    translating_agent: TranslatingAgent,
    *,
    show_progress: bool,
    parent: models.SummaryTopic,
) -> models.SummaryTopic: ...
def _summarize_structured_content(
    topic: models.ContentTopic,
    summarizing_agent: SummarizingAgent,
    translating_agent: TranslatingAgent,
    *,
    show_progress: bool,
    parent: models.SummaryTopic | None = None,
) -> models.SummaryTopic:
    """Summarizes structured content."""

    if show_progress and len(topic.subtopics) > 0:
        total = len(topic.subtopics) + 1
        pbar = tqdm(desc=f"{topic.level}. {topic.title}", total=total)
    else:
        pbar = None

    main_segment_summary = _summarize_unstructured_content(
        topic.main_segment,
        summarizing_agent,
        show_progress=show_progress,
    )
    if isinstance(topic, models.StructuredContent):
        summary = models.StructuredSummary(
            main_segment=main_segment_summary, subtopics=[]
        )
    else:
        topic_title = translating_agent.get_output(topic.title).translated_text

        summary = models.SummaryTopic(
            level=topic.level,
            title=topic_title,
            main_segment=main_segment_summary,
            subtopics=[],
            parent=parent,
        )

    if pbar:
        pbar.update()

    for subtopic in topic.subtopics:
        subtopic_summary = _summarize_structured_content(
            subtopic,
            summarizing_agent,
            translating_agent,
            show_progress=show_progress,
            parent=summary,
        )
        summary.subtopics.append(subtopic_summary)

        if pbar:
            pbar.update()

    if pbar:
        pbar.close()

    return summary


def summarize_content(
    content: models.Content,
    settings: SummarizingSettings,
    *,
    show_progress: bool,
) -> models.Summary:
    """Summarizes content."""

    logger.debug("Summarizing extracted content.")

    summarizing_agent = SummarizingAgent(
        api_settings=settings.llm_api,
        agent_settings=settings.summarizing_agent,
        lang=settings.lang,
        summary_type=settings.summary_type,
        detail=settings.detail,
        quality=settings.quality,
    )

    if show_progress:
        print("The application summarizes information from the source.")
        print("Please wait while the summary is being generated...")
        print()

    match content:
        case models.UnstructuredContent():
            summary = _summarize_unstructured_content(
                content,
                summarizing_agent,
                show_progress=show_progress,
            )
        case models.StructuredContent():
            translating_agent = TranslatingAgent(
                api_settings=settings.llm_api,
                agent_settings=settings.translating_agent,
                target_lang=settings.lang,
            )
            summary = _summarize_structured_content(
                content,
                summarizing_agent,
                translating_agent,
                show_progress=show_progress,
            )

    logger.debug("Extracted content summarized successfully.")

    return summary
