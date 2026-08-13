"""Building application bundle."""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1].resolve()
BUILDER_ROOT = Path(__file__).parent.resolve()

BUILD_ROOT = PROJECT_ROOT / "build"
DIST_ROOT = PROJECT_ROOT / "dist"

VCPKG_ROOT = BUILDER_ROOT / "vcpkg"
VCPKG_INSTALL_ROOT = BUILD_ROOT / "vcpkg_installed"


def build_bundle() -> None:
    """Builds application bundle."""

    vcpkg_bin = VCPKG_ROOT / (
        "vcpkg.exe" if sys.platform == "win32" else "vcpkg"
    )

    if sys.platform == "win32":
        triplet = "x64-windows-static"
    elif sys.platform == "darwin":
        triplet = "x64-osx"
    else:
        triplet = "x64-linux"

    triplet += "-release"

    print(f"--> Compiling static Tesseract via vcpkg ({triplet})...")

    subprocess.run(
        [
            str(vcpkg_bin),
            "install",
            f"--triplet={triplet}",
            f"--host-triplet={triplet}",
            f"--x-install-root={VCPKG_INSTALL_ROOT}",
            f"--x-manifest-root={BUILDER_ROOT}",
        ],
        check=True,
    )

    vcpkg_installed_tools = (
        VCPKG_INSTALL_ROOT / triplet / "tools" / "tesseract"
    )
    tesseract_exe_name = (
        "tesseract.exe" if sys.platform == "win32" else "tesseract"
    )
    tesseract_bin_path = vcpkg_installed_tools / tesseract_exe_name
    tesseract_bin_path = tesseract_bin_path.resolve()

    if not tesseract_bin_path.exists():
        print(
            f"Error: Could not find compiled tesseract binary at "
            f"{tesseract_bin_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"--> Found static binary: {tesseract_bin_path}")

    print("--> Building PyInstaller package...")

    os.environ["PROJECT_ROOT"] = str(PROJECT_ROOT)
    os.environ["BUILDER_ROOT"] = str(BUILDER_ROOT)
    os.environ["TESSERACT_BIN"] = str(tesseract_bin_path)

    subprocess.run(
        [
            "pyinstaller",
            "--workpath",
            BUILD_ROOT,
            "--distpath",
            DIST_ROOT,
            BUILDER_ROOT / "app.spec",
        ],
        check=True,
    )

    print("✅ Build complete! Check the 'dist' folder.")


if __name__ == "__main__":
    build_bundle()
