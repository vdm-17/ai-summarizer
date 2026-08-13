"""Config command."""

import logging
from pathlib import Path

from ai_summarizer.application.services import configurator

from .base import CommandsGroup

logger = logging.getLogger(__name__)
logger.propagate = False


config = CommandsGroup("config", description="Application config commands.")


@config.command()
def generate(
    *,
    output_dirname: Path | None = None,
) -> None:
    """Generates file with application config."""

    output_filename = configurator.generate_config(output_dirname)

    print()
    print(
        "Application config successfully generated at "
        f"{output_filename.resolve()}"
    )


@config.command()
def load(filename: Path) -> None:
    """Generates file with application config."""

    config = configurator.load_config(filename)
    output_filename = configurator.save_config(config)

    print()
    print(f"Loaded config successfully saved at {output_filename.resolve()}")
