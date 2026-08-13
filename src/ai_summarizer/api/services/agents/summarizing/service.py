"""The main service of the summarizing LLM agent."""

from openai.types.responses import ResponseInputParam
from tqdm import tqdm

from ai_summarizer.api import models
from ai_summarizer.api.services.agents.base import LLMAgent, ReasoningEffort
from ai_summarizer.api.settings import (
    Detail,
    LLMAPISettings,
    Quality,
    SummarizingAgentSettings,
    SummaryType,
)

from .data_preparing import (
    prepare_openai_input_data,
    split_content_into_chunks,
)
from .errors import AgentResponseError
from .instructions_loading import load_instructions
from .models import (
    ArbitraryTextOutput,
    QuestionsListOutput,
    SummarizingAgentOutput,
)


class SummarizingAgent(
    LLMAgent[models.UnstructuredContent, SummarizingAgentOutput]
):
    """Summarizing LLM agent."""

    def __init__(
        self,
        *,
        api_settings: LLMAPISettings,
        agent_settings: SummarizingAgentSettings,
        lang: str,
        summary_type: SummaryType,
        detail: Detail,
        quality: Quality,
    ) -> None:
        instructions = load_instructions(
            lang=lang, summary_type=summary_type, detail=detail
        )

        match summary_type:
            case SummaryType.arbitrary_text:
                self._output_type = ArbitraryTextOutput
            case SummaryType.questions_list:
                self._output_type = QuestionsListOutput

        match detail:
            case Detail.low:
                verbosity = "low"
            case Detail.medium:
                verbosity = "medium"
            case Detail.high:
                verbosity = "high"

        reasoning_effort: ReasoningEffort
        match quality:
            case Quality.low:
                reasoning_effort = "low"
            case Quality.medium:
                reasoning_effort = "medium"
            case Quality.high:
                reasoning_effort = "high"
            case Quality.max:
                reasoning_effort = "xhigh"

        super().__init__(
            name="Summarizing agent",
            api_key=api_settings.api_key,
            base_url=api_settings.base_url,
            instructions=instructions,
            model=agent_settings.model,
            max_output_tokens=agent_settings.max_output_tokens,
            context_size=agent_settings.context_size,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            output_type=self._output_type,
        )

        self._model = agent_settings.model
        self._max_input_tokens = agent_settings.max_input_tokens
        self._summary_type = summary_type

    def _get_openai_input_data(
        self, input_data: models.UnstructuredContent
    ) -> ResponseInputParam:
        return prepare_openai_input_data(input_data)

    def get_output(
        self,
        input_data: models.UnstructuredContent,
        *,
        show_progress: bool = False,
    ) -> SummarizingAgentOutput:
        """Returns agent output."""

        match self._summary_type:
            case SummaryType.arbitrary_text:
                agent_output = ArbitraryTextOutput(text="")
            case SummaryType.questions_list:
                agent_output = QuestionsListOutput(items=[])

        content_chunks = split_content_into_chunks(
            input_data,
            chunk_max_tokens=self._max_input_tokens,
            model=self._model,
        )

        if show_progress and len(content_chunks) > 1:
            chunks_pbar = tqdm(desc="Chunks", total=len(content_chunks))
        else:
            chunks_pbar = None

        for chunk in content_chunks:
            output_chunk = super().get_output(chunk)

            match agent_output:
                case ArbitraryTextOutput():
                    if not isinstance(output_chunk, ArbitraryTextOutput):
                        raise AgentResponseError

                    agent_output.text += output_chunk.text
                case QuestionsListOutput():
                    if not isinstance(output_chunk, QuestionsListOutput):
                        raise AgentResponseError

                    agent_output.items.extend(output_chunk.items)

            if chunks_pbar:
                chunks_pbar.update()

        if chunks_pbar:
            chunks_pbar.close()

        return agent_output
