"""Application configurator."""

import configparser
import os
from pathlib import Path

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_serializer,
    field_validator,
)

from ai_summarizer.api.settings import OCRQuality
from ai_summarizer.application.definitions import APP_DIRS

from .errors import InternalServiceError


def _tuple_to_string(v: tuple):
    """Converts tuple to comma-separated string."""
    return f"({', '.join(v)})"


def _string_to_tuple(v: str):
    """Converts comma-separated string to tuple."""
    return tuple(tag.strip() for tag in v[1:-1].split(",") if tag.strip())


class GeneralConfig(BaseModel):
    """General config."""

    llm_api_base_url: str = "https://api.openai.com/v1"
    structurizing_min_tokens: int = 10**4


class OCRConfig(BaseModel):
    """OCR config."""

    quality: OCRQuality = OCRQuality.medium
    langs: tuple[str, ...] = ("eng",)

    @field_serializer("langs")
    def serialize_langs(self, v: tuple[str]) -> str:
        return _tuple_to_string(v)

    @field_validator("langs", mode="before")
    def validate_langs(cls, v) -> tuple[str, ...]:
        if isinstance(v, str):
            return _string_to_tuple(v)
        return v


class SummarizingAgentConfig(BaseModel):
    """Summarizing agent config."""

    model: str = "gpt-5-mini"
    context_size: int = 2 * (10**5)
    max_input_tokens: int = 5 * (10**4)
    max_output_tokens: int = 4 * (10**4)


class TranslatingAgentConfig(BaseModel):
    """LLM config."""

    model: str = "gpt-5-nano"


class ApplicationConfig(BaseModel):
    """Application config."""

    general: GeneralConfig = Field(default_factory=GeneralConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    summarizing_agent: SummarizingAgentConfig = Field(
        default_factory=SummarizingAgentConfig
    )
    translating_agent: TranslatingAgentConfig = Field(
        default_factory=TranslatingAgentConfig
    )

    @property
    def ini_text(self) -> str:
        text = ""

        for section_name, section_config in self.model_dump().items():
            if not isinstance(section_config, dict):
                continue

            text += f"[{section_name.upper()}]\n"

            for key, value in section_config.items():
                text += f"{key}: {value}\n"

        return text


class ApplicationConfiguratorError(InternalServiceError):
    """Application configurator error."""


class ConfigSavingError(ApplicationConfiguratorError):
    """Error: unable to save application config."""


class ConfigLoadingError(ApplicationConfiguratorError):
    """Error: unable to load application config."""


class ConfigGenerationError(ApplicationConfiguratorError):
    """Error: unable to generate application config."""


def get_config_path() -> Path:
    return Path(
        os.getenv("CONFIG_PATH") or APP_DIRS.user_config_path / "config.ini"
    )


def save_config(
    config: ApplicationConfig,
    output_dirname: str | Path | None = None,
) -> Path:
    """Saves application config into file."""

    if output_dirname:
        output_filename = Path(output_dirname, "ai-summarizer-config.ini")
    else:
        output_filename = get_config_path()

    try:
        output_filename.parent.mkdir(parents=True, exist_ok=True)

        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(config.ini_text)
    except OSError:
        raise ConfigSavingError

    return output_filename


def generate_config(output_dirname: str | Path | None = None) -> Path:
    """Generates default application config."""

    default_config = ApplicationConfig()
    output_filename = save_config(default_config, output_dirname)

    return output_filename


def load_config(
    filename: str | Path | None = None,
) -> ApplicationConfig:
    """Loads application config."""

    if not filename:
        config_path = get_config_path()

        if config_path.exists():
            filename = config_path

    if not filename:
        return ApplicationConfig()

    parser = configparser.ConfigParser()

    try:
        parser.read(filename, encoding="utf-8")
    except configparser.Error as e:
        raise ConfigLoadingError from e

    config: dict[str, dict[str, object]] = {}

    for section_name in ApplicationConfig.model_fields.keys():
        upper_section_name = section_name.upper()

        if upper_section_name not in parser:
            continue

        parser_section = parser[upper_section_name]
        config[section_name] = {}

        for key, value in parser_section.items():
            config[section_name][key] = value

    try:
        return ApplicationConfig.model_validate(config)
    except ValidationError as e:
        raise ConfigLoadingError from e
