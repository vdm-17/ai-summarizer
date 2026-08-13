"""Building application installer."""

import os
import subprocess
import sys
import tomllib
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parents[1].resolve()
BUILDER_ROOT = Path(__file__).parent.resolve()

DIST_DIR = PROJECT_ROOT / "dist"
PYPROJECT_TOML_PATH = PROJECT_ROOT / "pyproject.toml"


def build_installer() -> None:
    """Builds application installer."""

    load_dotenv()
    project_info = tomllib.load(open(PYPROJECT_TOML_PATH, "rb"))["project"]

    os.environ["VERSION"] = project_info["version"]

    if sys.platform == "win32":
        iscc_bin_path = os.environ["ISCC_BIN"]

        subprocess.run(
            [
                iscc_bin_path,
                BUILDER_ROOT / "app.iss",
            ],
            check=True,
        )
    elif sys.platform == "darwin":
        pass
    else:
        DIST_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "nfpm",
                "package",
                "--config nfpm.yaml",
                "--target ../dist/",
            ],
            cwd=BUILDER_ROOT,
            check=True,
        )


if __name__ == "__main__":
    build_installer()
