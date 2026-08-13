"""Setting runtime environment."""

import os
import sys
from pathlib import Path

from pytesseract import pytesseract


def _get_bundle_root() -> Path:
    """Returns bundle root directory."""

    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))

    return Path(__file__).resolve().parent


def set_bundle_env() -> None:
    """Sets runtime environment variables for the application."""

    bundle_root = _get_bundle_root()

    tesseract_root = bundle_root / "bin"
    tesseract_bin_name = (
        "tesseract.exe" if sys.platform == "win32" else "tesseract"
    )
    tesseract_bin_path = tesseract_root / tesseract_bin_name

    pytesseract.tesseract_cmd = tesseract_bin_path
    os.environ["TESSERACT_CMD"] = str(tesseract_bin_path)


if __name__ == "__main__":
    set_bundle_env()
