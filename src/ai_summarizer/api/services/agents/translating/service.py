"""The main service of the summarizing LLM agent."""

from pydantic import BaseModel, Field

from ai_summarizer.api.services.agents.base import LLMAgent
from ai_summarizer.api.settings import LLMAPISettings, TranslatingAgentSettings

from .instructions_loading import load_instructions


class TranslatingAgentOutput(BaseModel):
    """Translating agent output."""

    translated_text: str = Field(description="Translated text.")


class TranslatingAgent(LLMAgent[str, TranslatingAgentOutput]):
    """Translating agent."""

    def __init__(
        self,
        target_lang: str,
        *,
        api_settings: LLMAPISettings,
        agent_settings: TranslatingAgentSettings,
    ) -> None:
        instructions = load_instructions(target_lang)

        super().__init__(
            name="Translating agent",
            api_key=api_settings.api_key,
            base_url=api_settings.base_url,
            instructions=instructions,
            model=agent_settings.model,
            reasoning_effort="low",
            verbosity="low",
            output_type=TranslatingAgentOutput,
        )

    def _get_openai_input_data(self, input_data: str) -> str:
        """Returns OpenAI input data."""
        return input_data

    def get_output(self, input_data: str) -> TranslatingAgentOutput:
        """Returns agent output."""

        return super().get_output(input_data)
