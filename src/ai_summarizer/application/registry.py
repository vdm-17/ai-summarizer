"""Application registry."""

import logging.config
import os
from pathlib import Path

from .commands import CommandsGroup, auth, config, summarize
from .definitions import (
    APP_DESCRIPTION,
    APP_DIRS,
    APP_NAME,
    AppEnvVar,
)


def _runtime_hook() -> None:
    """Application runtime hook."""

    tessdata_dir = Path(
        os.getenv(AppEnvVar.tessdata_dir)
        or APP_DIRS.user_data_path / "tessdata"
    )
    tessdata_dir.mkdir(parents=True, exist_ok=True)

    os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)

    log_dir = Path(os.getenv(AppEnvVar.log_dir) or APP_DIRS.user_log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_filename = log_dir / "app.log"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": log_format,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "detailed",
            },
            "rotating_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": log_filename,
                "maxBytes": 1024**2,
                "backupCount": 5,
                "encoding": "utf-8",
                "mode": "a",
            },
        },
        "loggers": {
            "ai_summarizer": {
                "handlers": ["console", "rotating_file"],
                "level": "DEBUG",
                "propagate": True,
            }
        },
    }

    logging.config.dictConfig(logging_config)


ai_summarizer_app = CommandsGroup(
    name=APP_NAME,
    description=APP_DESCRIPTION,
    runtime_hook=_runtime_hook,
)
ai_summarizer_app.add_commands(auth, config, summarize)
