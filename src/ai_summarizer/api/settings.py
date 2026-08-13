"""API settings."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence


class OCRQuality(StrEnum):
    """OCR quality."""

    low = "low"
    medium = "medium"
    high = "high"


class SummaryType(StrEnum):
    """Summary type."""

    arbitrary_text = "arbitrary-text"
    questions_list = "questions-list"


class Detail(StrEnum):
    """Summarizing detail."""

    low = "low"
    medium = "medium"
    high = "high"


class Quality(StrEnum):
    """Summarizing quality."""

    low = "low"
    medium = "medium"
    high = "high"
    max = "max"


@dataclass(slots=True, frozen=True, kw_only=True)
class OCRSettings:
    """OCR settings."""

    quality: OCRQuality
    langs: Sequence[str]


@dataclass(slots=True, frozen=True, kw_only=True)
class LLMAPISettings:
    """LLM API."""

    base_url: str
    api_key: str


@dataclass(slots=True, frozen=True, kw_only=True)
class SummarizingAgentSettings:
    """Summarizing agent settings."""

    model: str
    context_size: int
    max_input_tokens: int
    max_output_tokens: int


@dataclass(slots=True, frozen=True, kw_only=True)
class TranslatingAgentSettings:
    """Summarizing agent settings."""

    model: str


@dataclass(slots=True, frozen=True, kw_only=True)
class SummarizingSettings:
    """Summarizing settings."""

    ocr: OCRSettings
    llm_api: LLMAPISettings
    summarizing_agent: SummarizingAgentSettings
    translating_agent: TranslatingAgentSettings
    summary_type: SummaryType
    detail: Detail
    quality: Quality
    lang: str
    structurize: bool
    structurizing_min_tokens: int
