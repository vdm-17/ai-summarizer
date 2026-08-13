"""Application authenticator."""

import os

import keyring
from keyring.errors import (
    KeyringError,
    PasswordDeleteError,
    PasswordSetError,
)

from ..definitions import APP_NAME, AppEnvVar
from .errors import InternalServiceError


class ApplicationAuthenticatorError(InternalServiceError):
    """Application authenticator error."""


class AuthentificationError(ApplicationAuthenticatorError):
    """Authentification error."""


_LLM_API_USERNAME = "llm-api"


def login(llm_api_key: str) -> None:
    """Asks user for LLM API key and stores it for future use."""

    try:
        keyring.set_password(APP_NAME, _LLM_API_USERNAME, llm_api_key)
    except PasswordSetError as e:
        raise AuthentificationError from e


def logout() -> None:
    """Deletes stored LLM API key."""

    try:
        keyring.delete_password(APP_NAME, _LLM_API_USERNAME)
    except PasswordDeleteError as e:
        raise AuthentificationError from e


def get_credentials() -> str:
    """Returns stored LLM API key."""

    try:
        llm_api_key = keyring.get_password(APP_NAME, _LLM_API_USERNAME)
    except KeyringError:
        llm_api_key = None

    if llm_api_key:
        return llm_api_key

    llm_api_key = os.getenv(AppEnvVar.llm_api_key)

    if llm_api_key:
        return llm_api_key

    llm_api_key_file = os.getenv(AppEnvVar.llm_api_key_file)
    if llm_api_key_file:
        try:
            with open(llm_api_key_file, encoding="utf-8") as f:
                llm_api_key = f.read().strip()
        except OSError as e:
            raise AuthentificationError from e

    if llm_api_key:
        return llm_api_key

    raise AuthentificationError
