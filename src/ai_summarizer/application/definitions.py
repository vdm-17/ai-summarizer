"""Application definitions."""

from enum import StrEnum

from platformdirs import PlatformDirs

APP_NAME = "ai-summarizer"
APP_DESCRIPTION = "The utility for summarizing a source content using AI."
APP_DIRS = PlatformDirs(
    appname=APP_NAME,
    appauthor=False,
    opinion=True,
    ensure_exists=True,
)


class AppEnvVar(StrEnum):
    """Application environment variable."""

    llm_api_key = "LLM_API_KEY"
    llm_api_key_file = "LLM_API_KEY_FILE"
    log_dir = "LOG_DIR"
    config_path = "CONFIG_PATH"
    output_dir = "OUTPUT_DIR"
    tessdata_dir = "TESSDATA_DIR"
