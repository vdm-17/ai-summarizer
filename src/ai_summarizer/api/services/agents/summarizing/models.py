"""Data models of summarizing LLM agent."""

from pydantic import BaseModel, Field


class ArbitraryTextOutput(BaseModel):
    """Arbitrary text output."""

    text: str = Field(
        description="Text of a summary based on the provided source."
    )


class QuestionsListOutputItem(BaseModel):
    """Item of questions list output."""

    question: str = Field(
        description="A question based on the provided source."
    )
    answer: str = Field(
        description="The true answer to the relevant question."
    )
    answer_source_pages: list[int] = Field(
        description=(
            "A list of page numbers in the provided source from which "
            "the answer to the corresponding question was taken."
        )
    )
    answer_source_fragment: str = Field(
        description=(
            "A quote from the source that provided the answer to the "
            "corresponding question. The fragment must be accurate, "
            "and the language must be original."
        )
    )


class QuestionsListOutput(BaseModel):
    """Questions list output."""

    items: list[QuestionsListOutputItem] = Field(
        description="A list of questions and answers for self-monitoring."
    )


SummarizingAgentOutput = ArbitraryTextOutput | QuestionsListOutput
