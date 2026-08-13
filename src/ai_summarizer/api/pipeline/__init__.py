"""Summarizing pipeline."""

from .errors import SummarizingPipelineError
from .orchestrator import summarize_source

__all__ = [
    "summarize_source",
    "SummarizingPipelineError",
]
