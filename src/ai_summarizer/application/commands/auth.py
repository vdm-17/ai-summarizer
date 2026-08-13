"""Auth command."""

import logging

from pwinput import pwinput

from ai_summarizer.application.services import authenticator

from .base import CommandsGroup

logger = logging.getLogger(__name__)
logger.propagate = False


auth = CommandsGroup("auth", description=__doc__)


@auth.command()
def login() -> None:
    """Login to the application."""

    print()
    llm_api_key = pwinput("Your LLM API key: ")

    authenticator.login(llm_api_key)

    print()
    print("The authentication login successfully.")


@auth.command()
def logout() -> None:
    """Logout from the application."""

    authenticator.logout()

    print()
    print("The authentication logout successfully.")
