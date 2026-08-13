"""Errors of the summarizing LLM agent."""

from ..errors import LLMAgentError


class SummarizingAgentError(LLMAgentError):
    """Summarizing LLM agent error."""


class AgentResponseError(SummarizingAgentError):
    """Error: invalid agent response."""
