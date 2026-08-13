"""LLM agent."""

from abc import ABC, abstractmethod
from typing import Literal

import agents
import openai
from openai.types import ReasoningEffort
from openai.types.responses import ResponseInputParam

from .errors import LLMAgentError


class LLMAgent[AgentInput, AgentOutput](ABC):
    """LLM agent."""

    def __init__(
        self,
        *,
        name: str,
        api_key: str,
        base_url: str,
        instructions: str,
        model: str,
        context_size: int | None = None,
        max_output_tokens: int | None = None,
        reasoning_effort: ReasoningEffort,
        verbosity: Literal["low", "medium", "high"],
        output_type: type[AgentOutput],
    ) -> None:
        self.name = name
        openai_client = openai.AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            max_retries=5,
        )
        agents.set_default_openai_client(openai_client)
        agents.set_tracing_disabled(True)

        model_settings = agents.ModelSettings(
            context_management=[
                {
                    "type": "compaction",
                    "compact_threshold": context_size,
                }
            ],
            reasoning=openai.types.Reasoning(effort=reasoning_effort),
            verbosity=verbosity,
            max_tokens=max_output_tokens,
            store=False,
        )

        self._openai_agent = agents.Agent(
            name=self.name,
            instructions=instructions,
            model=model,
            model_settings=model_settings,
            output_type=output_type,
        )
        self._output_type = output_type

        if context_size:
            self._openai_session = agents.SQLiteSession(name)
        else:
            self._openai_session = None

    @abstractmethod
    def _get_openai_input_data(
        self, input_data: AgentInput
    ) -> str | ResponseInputParam:
        """Returns OpenAI input data."""

        raise NotImplementedError

    @abstractmethod
    def get_output(
        self,
        input_data: AgentInput,
    ) -> AgentOutput:
        """Returns agent output."""

        openai_input_data = self._get_openai_input_data(input_data)

        try:
            return agents.Runner.run_sync(
                self._openai_agent,
                openai_input_data,
                session=self._openai_session,
            ).final_output_as(self._output_type, True)
        except (agents.exceptions.AgentsException, openai.OpenAIError) as e:
            raise LLMAgentError from e
