"""Loading instructions for summarizing LLM agent."""

from pathlib import Path

import yaml

from .errors import TranslatingAgentError

INSTRUCTIONS_PATH = Path(__file__).parent / "instructions.yaml"


class InstructionsLoadingError(TranslatingAgentError):
    """Error: unable to load instructions for translating agent."""


def load_instructions(target_lang: str) -> str:
    """Loads instructions for the summarizing agent."""

    try:
        with open(INSTRUCTIONS_PATH) as f:
            doc = f.read()
    except OSError as e:
        raise InstructionsLoadingError from e

    try:
        all_instructions = yaml.safe_load(doc)
    except yaml.error.YAMLError as e:
        raise InstructionsLoadingError from e

    if not isinstance(all_instructions, dict):
        raise InstructionsLoadingError

    general_key = "general"

    if general_key not in all_instructions:
        raise InstructionsLoadingError

    general_instructions = all_instructions[general_key]
    if not isinstance(general_instructions, str):
        raise InstructionsLoadingError

    return general_instructions.format(target_lang=target_lang)
