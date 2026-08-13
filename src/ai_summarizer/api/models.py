"""API data models."""

from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, dataclass, field
from typing import Literal, Protocol, Sequence


class ContentUnit(Protocol):
    """Content unit."""

    @property
    def start_page(self) -> int | None: ...
    @property
    def end_page(self) -> int | None: ...


@dataclass(slots=True, kw_only=True)
class ContentBaseUnit:
    """Base unit of content."""

    start_page: int | None = None
    end_page: int | None = None


@dataclass(slots=True)
class TextBlock(ContentBaseUnit):
    """Block of text content."""

    text: str


ImageDetail = Literal["low", "auto", "high", "original"]


@dataclass(slots=True)
class Image(ContentBaseUnit):
    """Unit of image content."""

    data: bytes
    _: KW_ONLY
    detail: ImageDetail = "low"
    alt: str = ""


class PageEndAnchor(ContentBaseUnit):
    """Metadata anchor of content page end."""


class ContentUnitsGroup(ABC):
    """Group of content units."""

    @abstractmethod
    def _units(self) -> Sequence[ContentUnit]:
        """Returns content units."""
        raise NotImplementedError

    @property
    def start_page(self) -> int | None:
        """Returns start page of content units."""

        units = self._units()
        return units[0].start_page if units else None

    @property
    def end_page(self) -> int | None:
        """Returns end page of content units."""

        units = self._units()
        return units[-1].end_page if units else None


@dataclass(slots=True)
class Heading(ContentUnitsGroup):
    """Content heading."""

    units: list[ContentBaseUnit]
    level: int

    def _units(self) -> list[ContentBaseUnit]:
        """Returns content units."""
        return self.units


@dataclass(slots=True)
class Paragraph(ContentUnitsGroup):
    """Content paragraph."""

    units: list[ContentBaseUnit]

    def _units(self) -> list[ContentBaseUnit]:
        """Returns content units."""
        return self.units


@dataclass(slots=True)
class UnstructuredContent(ContentUnitsGroup):
    """Unstructured content."""

    units: list[Heading | Paragraph]

    def _units(self) -> list[Heading | Paragraph]:
        """Returns content units."""
        return self.units


@dataclass(slots=True, kw_only=True)
class ContentTopic(ContentUnitsGroup):
    """Content topic."""

    title: str
    level: int
    main_segment: UnstructuredContent
    subtopics: list[ContentTopic]
    parent: ContentTopic | None

    def _units(self) -> list[UnstructuredContent | ContentTopic]:
        """Returns content units."""
        return [self.main_segment, *self.subtopics]


@dataclass(slots=True)
class StructuredContent(ContentTopic):
    """Structured content."""

    title: str = field(default="Content", init=False)
    parent: ContentTopic | None = field(default=None, init=False)
    level: int = field(default=1, init=False)


Content = UnstructuredContent | StructuredContent


@dataclass(slots=True, frozen=True)
class ArbitraryTextSummary:
    """Summary of arbitrary text type."""

    md_text: str


@dataclass(slots=True, frozen=True)
class QuestionsListSummaryItem:
    """Item of questions list summary."""

    question: str
    answer: str
    _: KW_ONLY
    answer_source_pages: list[int]
    answer_source_fragment: str

    @property
    def md_text(self) -> str:
        """Returns text of summary."""

        pages = ", ".join([str(p) for p in self.answer_source_pages])
        return (
            f"Question: {self.question} "
            f"Answer: ||{self.answer}|| "
            f"Pages: {pages}. "
            f"Source_fragment: ||{self.answer_source_fragment}||\n"
        )


@dataclass(slots=True, frozen=True)
class QuestionsListSummary:
    """Summary of questions list type."""

    items: list[QuestionsListSummaryItem]

    @property
    def md_text(self) -> str:
        """Returns summary text."""

        text = ""
        for i, item in enumerate(self.items):
            text += f"{i + 1}. {item.md_text}"

        return text


@dataclass(slots=True, frozen=True)
class UnstructuredSummary:
    """Unstructured summary"""

    unit: ArbitraryTextSummary | QuestionsListSummary

    @property
    def md_text(self) -> str:
        """Returns summary text."""
        return self.unit.md_text + "\n"


@dataclass(slots=True, frozen=True, kw_only=True)
class SummaryTopic:
    """Summary topic."""

    title: str
    level: int
    main_segment: UnstructuredSummary
    subtopics: list[SummaryTopic]
    parent: SummaryTopic | None

    @property
    def md_text(self) -> str:
        """Returns summary text."""

        summary_text = f"{'#' * self.level} {self.title}\n\n"
        summary_text += self.main_segment.md_text

        for subtopic in self.subtopics:
            summary_text += "\n" + subtopic.md_text

        return summary_text


@dataclass(slots=True, frozen=True, kw_only=True)
class StructuredSummary(SummaryTopic):
    """Structured summary."""

    title: str = field(default="Summary", init=False)
    level: int = field(default=1, init=False)
    parent: SummaryTopic | None = field(default=None, init=False)


Summary = UnstructuredSummary | StructuredSummary
