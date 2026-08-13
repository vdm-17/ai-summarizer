# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

APP_NAME = "ai-summarizer"

PACKAGES_WITH_DATA = [
    "ai_summarizer",
    "pymupdf",
    "pymupdf4llm",
    "rapidocr_onnxruntime",
    "agents",
]
PACKAGES_WITH_HIDDEN_IMPORTS = [
    "tiktoken",
    "tiktoken_ext",
]

project_root = Path(os.environ["PROJECT_ROOT"])
builder_root = Path(os.environ["BUILDER_ROOT"])

tesseract_bin_path = os.environ["TESSERACT_BIN"]

datas = []
for package in PACKAGES_WITH_DATA:
    datas += collect_data_files(package)

hiddenimports = ["tiktoken_ext.openai_public"]
for package in PACKAGES_WITH_HIDDEN_IMPORTS:
    hiddenimports += collect_submodules(package)

a = Analysis(
    [str(project_root / "src" / "ai_summarizer" / "cli.py")],
    pathex=[],
    binaries=[(tesseract_bin_path, "bin")],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(builder_root / "set_runtime_env.py")],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
