"""CLI entry point to the application."""

import sys
from argparse import ArgumentParser, BooleanOptionalAction
from enum import StrEnum
from inspect import Parameter, signature
from typing import Any, Union, get_args

from ai_summarizer.application import (
    ApplicationError,
    CommandsGroup,
    ai_summarizer_app,
)
from ai_summarizer.errors import AISummarizerError

_COMMANDS_CHAIN_KEY = "commands_chain"


def register_commands(
    group: CommandsGroup,
    parser: ArgumentParser,
) -> None:
    """Registers application commands to parser."""

    commands_chain = parser.get_default(_COMMANDS_CHAIN_KEY) or []
    commands_chain = [name for name in commands_chain if isinstance(name, str)]

    subparsers = parser.add_subparsers(required=True)

    for command in group.commands.values():
        command_parser = subparsers.add_parser(
            command.name, description=command.description, help=command.help
        )
        command_parser.set_defaults(
            **{_COMMANDS_CHAIN_KEY: [*(commands_chain or []), command.name]}
        )

        if isinstance(command, CommandsGroup):
            register_commands(command, command_parser)
        else:
            command_params = signature(command.run).parameters
            short_names: dict[str, str] = {}

            for param_name in command_params.keys():
                param_short_name = "".join(
                    tag[0] for tag in param_name.split("_")
                )

                if param_short_name in short_names.values():
                    for key, value in short_names.items():
                        if value == param_short_name:
                            del short_names[key]
                elif param_short_name != "h":
                    short_names[param_name] = param_short_name

            for param in command_params.values():
                if param.annotation is Parameter.empty:
                    raise ApplicationError

                if isinstance(param.annotation, Union):
                    annotation_types = get_args(param.annotation)
                    param_type = [
                        t for t in annotation_types if t is not type(None)
                    ][0]
                else:
                    param_type = param.annotation

                cli_param_names: list[str] = []
                cli_param_settings: dict[str, Any] = {}

                if (
                    param.kind == param.POSITIONAL_OR_KEYWORD
                    or param.kind == param.POSITIONAL_ONLY
                ):
                    cli_param_names.append(param.name)
                    cli_param_settings["type"] = param_type
                else:
                    cli_param_names.append(f"--{param.name.replace('_', '-')}")

                    if param.name in short_names:
                        cli_param_names.append(f"-{short_names[param.name]}")

                    cli_param_settings["default"] = param.default

                    if param_type is bool:
                        cli_param_settings["action"] = BooleanOptionalAction
                    else:
                        cli_param_settings["type"] = param_type

                if param_type is StrEnum:
                    cli_param_settings["choices"] = param_type

                command_parser.add_argument(
                    *cli_param_names, **cli_param_settings
                )


def main() -> int:
    """Runs the application from CLI."""

    parser = ArgumentParser(
        ai_summarizer_app.name, description=ai_summarizer_app.description
    )
    register_commands(ai_summarizer_app, parser)

    args = vars(parser.parse_args())
    commands_chain: list[str] = []

    if _COMMANDS_CHAIN_KEY in args:
        commands_chain = args.pop(_COMMANDS_CHAIN_KEY)
        commands_chain = [
            name for name in commands_chain if isinstance(name, str)
        ]

    try:
        ai_summarizer_app(commands_chain, **args)
    except AISummarizerError as e:
        print(e, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
