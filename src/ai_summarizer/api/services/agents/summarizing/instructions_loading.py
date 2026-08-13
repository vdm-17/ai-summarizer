"""Loading instructions for summarizing LLM agent."""

from pathlib import Path

import yaml
from langcodes import Language
from langcodes.tag_parser import LanguageTagError

from ai_summarizer.api.settings import Detail, SummaryType

from .errors import SummarizingAgentError

INSTRUCTIONS_PATH = Path(__file__).parent / "instructions.yaml"


class InstructionsLoadingError(SummarizingAgentError):
    """Error: unable to load instructions for summarizing agent."""


def _get_summary_type_instructions(
    summary_type: SummaryType, options: dict[object, object]
) -> str:
    """Returns parsed instructions for specific summarizing formats."""

    match summary_type:
        case SummaryType.arbitrary_text:
            value_key = "arbitrary-text"
        case SummaryType.questions_list:
            value_key = "questions-list"

    if value_key not in options:
        raise InstructionsLoadingError

    instructions = options[value_key]

    if not isinstance(instructions, str):
        raise InstructionsLoadingError

    return instructions


def _get_detail_instructions(
    detail: Detail, options: dict[object, object]
) -> str:
    """Returns parsed instructions for levels of summarizing details."""

    match detail:
        case Detail.low:
            value_key = "low"
        case Detail.medium:
            value_key = "medium"
        case Detail.high:
            value_key = "high"

    if value_key not in options:
        raise InstructionsLoadingError

    instructions = options[value_key]

    if not isinstance(instructions, str):
        raise InstructionsLoadingError

    return instructions


def load_instructions(
    *, lang: str, summary_type: SummaryType, detail: Detail
) -> str:
    """Loads instructions for the translating agent."""

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
    lang_key = "lang"
    summary_type_key = "summary-type"
    detail_key = "detail"

    if (
        general_key not in all_instructions
        or lang_key not in all_instructions
        or summary_type_key not in all_instructions
        or detail_key not in all_instructions
    ):
        raise InstructionsLoadingError

    general_instructions = all_instructions[general_key]
    if not isinstance(general_instructions, str):
        raise InstructionsLoadingError

    lang_instructions = all_instructions[lang_key]
    if not isinstance(lang_instructions, str):
        raise InstructionsLoadingError

    try:
        lang_name = Language.get(lang).language_name().lower()
    except LanguageTagError as e:
        raise InstructionsLoadingError from e

    lang_instructions = lang_instructions.format(lang_name=lang_name)

    summary_type_options = all_instructions[summary_type_key]
    if not isinstance(summary_type_options, dict):
        raise InstructionsLoadingError

    detail_options = all_instructions[detail_key]
    if not isinstance(detail_options, dict):
        raise InstructionsLoadingError

    summary_type_instructions = _get_summary_type_instructions(
        summary_type, summary_type_options
    )
    detail_instructions = _get_detail_instructions(detail, detail_options)

    return "{} {} {} {}".format(
        general_instructions,
        lang_instructions,
        summary_type_instructions,
        detail_instructions,
    )
