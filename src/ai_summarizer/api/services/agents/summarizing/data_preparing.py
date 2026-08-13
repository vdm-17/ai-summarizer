"""Preparing input data for OpenAI model."""

from base64 import b64encode

from openai.types.responses import (
    ResponseInputImageParam,
    ResponseInputMessageContentListParam,
    ResponseInputParam,
    ResponseInputTextParam,
)

from ai_summarizer.api import models
from ai_summarizer.api.services.tokens_counter import count_content_tokens

from .errors import SummarizingAgentError


class ContentSplittingError(SummarizingAgentError):
    """Error: unable to split content into chunks."""


class UnstructuredContentLimitError(ContentSplittingError):
    """
    Error: too long unstructured content part.

    All long content parts must be divided into paragraphs or topics.
    """


def split_content_into_chunks(
    content: models.UnstructuredContent,
    *,
    chunk_max_tokens: int,
    model: str,
) -> list[models.UnstructuredContent]:
    """
    Splits content into chunks based on tokens count.

    Each segment will contain as many paragraphs as possible without exceeding
    the maximum token limit for the model. If a single paragraph exceeds the
    token limit, an error is raised.
    """

    chunks: list[models.UnstructuredContent] = []
    current_chunk = models.UnstructuredContent([])
    current_chunk_tokens_count = 0

    for unit in content.units:
        unit_tokens_count = count_content_tokens(
            models.UnstructuredContent([unit]),
            llm_model=model,
        )

        if unit_tokens_count >= chunk_max_tokens:
            raise UnstructuredContentLimitError()

        new_tokens_count = current_chunk_tokens_count + unit_tokens_count

        if new_tokens_count < chunk_max_tokens:
            current_chunk.units.append(unit)
            current_chunk_tokens_count = new_tokens_count
        else:
            chunks.append(current_chunk)

            current_chunk = models.UnstructuredContent([unit])
            current_chunk_tokens_count = unit_tokens_count

    if current_chunk_tokens_count:
        chunks.append(current_chunk)

    return chunks


def prepare_openai_input_data(
    content: models.UnstructuredContent,
) -> ResponseInputParam:
    """Returns prepared input data for OpenAI model."""

    user_content: ResponseInputMessageContentListParam = []
    start_page = content.start_page
    end_page = content.end_page

    for units_group in content.units:
        match units_group:
            case models.Paragraph():
                group_start_message = "<!--paragraph start-->"
            case models.Heading():
                group_start_message = "<!--heading start-->"

        user_content.append(
            ResponseInputTextParam(type="input_text", text=group_start_message)
        )

        for base_unit in units_group.units:
            match base_unit:
                case models.TextBlock():
                    user_content.append(
                        ResponseInputTextParam(
                            type="input_text", text=base_unit.text
                        )
                    )
                case models.Image():
                    b64_image = b64encode(base_unit.data).decode()
                    user_content.append(
                        ResponseInputImageParam(
                            type="input_image",
                            image_url=f"data:image/png;base64,{b64_image}",
                            detail=base_unit.detail,
                        )
                    )
                case models.PageEndAnchor():
                    page_end_message = f"<!--page {base_unit.end_page} end-->"
                    user_content.append(
                        ResponseInputTextParam(
                            type="input_text", text=page_end_message
                        )
                    )

    input_data: ResponseInputParam = []

    if start_page is not None or end_page is not None:
        input_data.append(
            {
                "role": "system",
                "content": f"Start page: {start_page}. End page: {end_page}",
            }
        )

    input_data.append({"role": "user", "content": user_content})

    return input_data
