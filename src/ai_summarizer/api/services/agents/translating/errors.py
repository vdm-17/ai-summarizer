"""Errors of the summarizing LLM agent."""

from ..errors import LLMAgentError


class TranslatingAgentError(LLMAgentError):
    """Translating agent error."""


class AgentResponseError(TranslatingAgentError):
    """Error: invalid agent response."""
