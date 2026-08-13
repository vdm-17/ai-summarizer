"""The main service of the content tokens counter."""

import tiktoken

from ai_summarizer.api import models

from .images import count_image_tokens

_UNIVERSAL_FALLBACK_ENCODING = "o200k_base"


def count_text_tokens(text: str, llm_model: str) -> int:
    try:
        encoding = tiktoken.encoding_for_model(llm_model)
    except KeyError:
        encoding = tiktoken.get_encoding(_UNIVERSAL_FALLBACK_ENCODING)

    return len(encoding.encode(text))


def _count_unstructured_content_tokens(
    content: models.UnstructuredContent,
    llm_model: str,
) -> int:
    """Roughly estimates content tokens count for OpenAI model."""

    tokens_count = 0

    for units_group in content.units:
        for base_unit in units_group.units:
            match base_unit:
                case models.TextBlock():
                    tokens_count += count_text_tokens(
                        base_unit.text, llm_model
                    )
                case models.Image():
                    tokens_count += count_image_tokens(
                        base_unit.data,
                        llm_model,
                        detail=base_unit.detail,
                    )

    return tokens_count


def _count_topic_tokens(
    topic: models.ContentTopic,
    llm_model: str,
) -> int:
    tokens_count = _count_unstructured_content_tokens(
        topic.main_segment,
        llm_model,
    )

    for subtopic in topic.subtopics:
        tokens_count += _count_topic_tokens(
            subtopic,
            llm_model,
        )

    return tokens_count


def count_content_tokens(
    content: models.Content | models.ContentTopic,
    llm_model: str,
) -> int:
    match content:
        case models.UnstructuredContent():
            return _count_unstructured_content_tokens(
                content,
                llm_model,
            )
        case models.ContentTopic():
            return _count_topic_tokens(content, llm_model)
