"""Commands base."""

from collections.abc import Callable
from typing import Concatenate, Generic, ParamSpec

from pydantic import validate_call

from .errors import CommandError

CommandParams = ParamSpec("CommandParams")
CommandRunner = Callable[CommandParams, None]


class UnknownCommandError(CommandError):
    """Error: given unknown command name."""


class Command(Generic[CommandParams]):
    """Command."""

    name: str
    description: str | None
    help: str | None
    run: CommandRunner

    def __init__(
        self,
        run: CommandRunner,
        *,
        name: str | None = None,
        description: str | None = None,
        help: str | None = None,
    ) -> None:
        self.run = run
        self.name = name or run.__name__
        self.description = description or run.__doc__
        self.help = help

    def __call__(
        self, *args: CommandParams.args, **kwargs: CommandParams.kwargs
    ) -> None:
        self.run(*args, **kwargs)


def command(
    name: str | None = None,
    description: str | None = None,
    help: str | None = None,
) -> Callable[[CommandRunner], Command[CommandParams]]:
    """Returns command creator."""

    def create_command(run: CommandRunner) -> Command[CommandParams]:
        """Creates command from function."""

        return Command(
            run=run,
            name=name,
            description=description,
            help=help,
        )

    return create_command


class CommandsGroup(Command[Concatenate[list[str], ...]]):
    """Commands group."""

    def __init__(
        self,
        name: str,
        *,
        commands: dict[str, Command] | None = None,
        runtime_hook: Callable[[], None] | None = None,
        description: str | None = None,
        help: str | None = None,
    ) -> None:
        super().__init__(
            self.run_command, name=name, description=description, help=help
        )

        self.commands: dict[str, Command] = commands or {}
        self._runtime_hook = runtime_hook

    def run_command(self, commands_chain: list[str], *args, **kwargs) -> None:
        """Runs selected command."""

        if not commands_chain:
            raise UnknownCommandError

        command_tag = commands_chain[0]
        if command_tag not in self.commands:
            raise UnknownCommandError

        command = self.commands[command_tag]

        if self._runtime_hook:
            self._runtime_hook()

        if isinstance(command, CommandsGroup):
            command(commands_chain[1:], *args, **kwargs)
        else:
            validate_call(command.run)(*args, **kwargs)

    def add_commands(self, *commands: Command):
        """Adds commands to group."""

        for c in commands:
            self.commands[c.name] = c

    def command(
        self,
        name: str | None = None,
        description: str | None = None,
        help: str | None = None,
    ) -> Callable[[CommandRunner], Command[CommandParams]]:
        """Returns creator of group command."""

        get_command = command(
            name=name,
            description=description,
            help=help,
        )

        def add_command(
            run: CommandRunner,
        ) -> Command[CommandParams]:
            """Creates command from function and adds it to group."""

            command = get_command(run)
            self.add_commands(command)

            return command

        return add_command
