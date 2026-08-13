"""Content structurizing."""

import logging

from ai_summarizer.api import models
from ai_summarizer.api.services.tokens_counter import count_content_tokens
from ai_summarizer.api.settings import SummarizingSettings

from .errors import SummarizingPipelineError

logger = logging.getLogger(__name__)


class ContentStructurizingError(SummarizingPipelineError):
    """Error: unable to structurize given content."""


class HeadingLevelError(ContentStructurizingError):
    """Heading level error."""

    def __init__(self, level: int) -> None:
        message = f"Error: {level} is invalid heading level."
        super().__init__(message)


def _combine_all_subtopics(topic: models.ContentTopic) -> None:
    """Combines all subtopics into main segment."""

    for s in topic.subtopics:
        _combine_all_subtopics(s)
        topic.main_segment.units.extend(s.main_segment.units)

    topic.subtopics.clear()


def _combine_small_subtopics(
    topic: models.ContentTopic,
    *,
    llm_model: str,
    min_tokens: int,
) -> None:
    """Combines small subtopics."""

    tokens_count = count_content_tokens(
        topic,
        llm_model,
    )

    if tokens_count < min_tokens:
        return _combine_all_subtopics(topic)

    for subtopic in topic.subtopics:
        _combine_small_subtopics(
            subtopic,
            llm_model=llm_model,
            min_tokens=min_tokens,
        )


def structurize_content(
    content: models.UnstructuredContent,
    settings: SummarizingSettings,
) -> models.StructuredContent:
    """Structurizes content into topics tree."""

    logger.debug("Structurizing extracted content.")

    structured_content = models.StructuredContent(
        main_segment=models.UnstructuredContent([]),
        subtopics=[],
    )
    current_topic: models.ContentTopic = structured_content

    for unit in content.units:
        if isinstance(unit, models.Heading):
            topic_level = unit.level + 1
            while True:
                if topic_level > current_topic.level:
                    break

                if current_topic.parent is None:
                    raise HeadingLevelError(unit.level)

                current_topic = current_topic.parent

            topic_title = "".join(
                u.text for u in unit.units if isinstance(u, models.TextBlock)
            )

            parent_topic = current_topic
            current_topic = models.ContentTopic(
                title=topic_title,
                level=topic_level,
                main_segment=models.UnstructuredContent([]),
                subtopics=[],
                parent=current_topic,
            )
            parent_topic.subtopics.append(current_topic)

        current_topic.main_segment.units.append(unit)

    _combine_small_subtopics(
        structured_content,
        llm_model=settings.summarizing_agent.model,
        min_tokens=settings.structurizing_min_tokens,
    )

    logger.debug("Extracted content structurized successfully.")

    return structured_content
