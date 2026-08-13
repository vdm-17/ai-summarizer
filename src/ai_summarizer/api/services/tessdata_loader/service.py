"""Tesseract-OCR data loader."""

import hashlib
import json
import logging
import os
import shutil
import tempfile
from enum import StrEnum
from pathlib import Path

import requests
from langcodes import Language
from langcodes.tag_parser import LanguageTagError

from .errors import (
    LanguageTrainedDataLoadingError,
    TessdataPrefixNotSpecifiedError,
    TrainedDataSHA256LoadingError,
)

logger = logging.getLogger(__name__)


class TessdataQuality(StrEnum):
    """Quality of loading tessdata."""

    default = "default"
    fast = "fast"
    best = "best"


DEFAULT_TESSDATA_QUALITY = TessdataQuality.default

_REPOS_URL = "https://raw.githubusercontent.com/tesseract-ocr/"

_DEFAULT_TESSDATA_REPO = "tessdata/ced78752cc61322fb554c280d13360b35b8684e4/"
_FAST_TESSDATA_REPO = "tessdata_fast/87416418657359cb625c412a48b6e1d6d41c29bd/"
_BEST_TESSDATA_REPO = "tessdata_best/e12c65a915945e4c28e237a9b52bc4a8f39a0cec/"

_TRAINEDDATA_SHA_256_DIR = Path(__file__).parent / "traineddata_sha256"


def _load_traineddata_sha256(lang: str, quality: TessdataQuality) -> str:
    """Loads sha256 for lang traineddata."""

    try:
        with open(_TRAINEDDATA_SHA_256_DIR / f"{quality}.json") as f:
            traineddata_sha256 = json.load(f)
            if not isinstance(traineddata_sha256, dict):
                raise TrainedDataSHA256LoadingError
    except OSError as e:
        raise TrainedDataSHA256LoadingError from e

    target_sha256 = traineddata_sha256[f"{lang}.traineddata"]
    if not isinstance(target_sha256, str):
        raise TrainedDataSHA256LoadingError

    return target_sha256


def load_traineddata(
    lang: str, quality: TessdataQuality = DEFAULT_TESSDATA_QUALITY
) -> None:
    """Loads language traineddata for the Tesseract-OCR."""

    try:
        lang = Language.get(lang).to_alpha3()
    except LanguageTagError as e:
        raise LanguageTrainedDataLoadingError from e

    logger.debug("Loading language traineddata for the Tesseract-OCR.")

    tessdata_prefix = os.getenv("TESSDATA_PREFIX")

    if not tessdata_prefix:
        raise TessdataPrefixNotSpecifiedError

    tessdata_dir = Path(tessdata_prefix)
    tessdata_dir.mkdir(parents=True, exist_ok=True)

    target = f"{lang}.traineddata"
    target_filename = Path(tessdata_prefix) / target
    target_sha256 = _load_traineddata_sha256(lang, quality)

    if target_filename.exists():
        with open(target_filename, "rb") as f:
            exists_data = f.read()

        exists_data_sha256 = hashlib.sha256(exists_data).hexdigest()

        if exists_data_sha256 == target_sha256:
            return

    match quality:
        case TessdataQuality.default:
            repo = _DEFAULT_TESSDATA_REPO
        case TessdataQuality.fast:
            repo = _FAST_TESSDATA_REPO
        case TessdataQuality.best:
            repo = _BEST_TESSDATA_REPO

    url = f"{_REPOS_URL}/{repo}/{target}"

    try:
        response = requests.get(url, timeout=(5, 15))
        response.raise_for_status()
    except (
        requests.Timeout,
        requests.HTTPError,
    ) as e:
        raise LanguageTrainedDataLoadingError from e

    response_content_sha256 = hashlib.sha256(response.content).hexdigest()

    if response_content_sha256 != target_sha256:
        raise LanguageTrainedDataLoadingError

    try:
        with tempfile.NamedTemporaryFile(
            dir=target_filename.parent, delete=False, suffix=".tmp"
        ) as tmp_file:
            tmp_file.write(response.content)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            temp_path = tmp_file.name

        shutil.move(temp_path, target_filename)
    except OSError as e:
        raise LanguageTrainedDataLoadingError from e

    logger.debug(
        "Language traineddata for the TesseractOCR loaded successfully."
    )
