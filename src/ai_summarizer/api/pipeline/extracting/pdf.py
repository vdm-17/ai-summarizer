"""Content extracting from PDF."""

import re
from pathlib import Path

from ai_summarizer.api import models
from ai_summarizer.api.services import tessdata_loader
from ai_summarizer.api.settings import OCRQuality, OCRSettings

from .errors import ContentExtractingError
from .md import extract_content_from_md_text

_SENTENCE_END_RE = re.compile(r'[.!?…:;)"»\]]$')


class PDFExtractingError(ContentExtractingError):
    """Error: unable to extract content from the given PDF document."""


def _is_sentence_end(text: str) -> bool:
    """Determines if a text string ends with a sentence-ending punctuation."""
    return bool(text and _SENTENCE_END_RE.search(text))


def _should_split_on_page_boundary(
    page_content: models.UnstructuredContent,
    prev_content: models.UnstructuredContent,
) -> bool:
    """Determines whether to split paragraph on page boundary."""

    if not page_content.units:
        return False
    if not prev_content.units:
        return False

    page_first_unit = page_content.units[0]
    prev_content_last_unit = prev_content.units[-1]

    if isinstance(page_first_unit, models.Heading):
        if isinstance(prev_content_last_unit, models.Heading):
            return page_first_unit.level != prev_content_last_unit.level
        return True
    if isinstance(prev_content_last_unit, models.Heading):
        return True

    if not page_first_unit.units:
        return True
    if not prev_content_last_unit.units:
        return True

    if isinstance(prev_content_last_unit.units[-1], models.TextBlock):
        prev_page_text = prev_content_last_unit.units[-1].text.strip()

        if (
            prev_page_text.endswith("-")
            or prev_page_text.endswith("–")
            or prev_page_text.endswith("—")
        ):
            return False

        return _is_sentence_end(prev_page_text)

    if isinstance(prev_content_last_unit.units[-1], models.Image):
        if isinstance(page_first_unit.units[0], models.Image):
            return False
        if isinstance(page_first_unit.units[0], models.TextBlock):
            page_text = page_first_unit.units[0].text.strip()

            if not page_text:
                return False

            return page_text[0].isupper()

    return True


def _specify_content_page(
    content: models.UnstructuredContent | models.Heading | models.Paragraph,
    page_num: int,
) -> None:
    """Specifies page metadata for content units."""

    for unit in content.units:
        match unit:
            case models.ContentBaseUnit():
                unit.start_page = page_num
                unit.end_page = page_num
            case models.ContentUnitsGroup():
                _specify_content_page(unit, page_num)


def extract_content_from_pdf(
    filename: str | Path,
    *,
    image_detail: models.ImageDetail,
    ocr_settings: OCRSettings,
    show_progress: bool,
) -> models.UnstructuredContent:
    """Extracts content from PDF document."""

    import pymupdf4llm
    import pytesseract
    from pymupdf4llm.ocr import rapidtess_api

    available_ocr_langs = [
        lang for lang in pytesseract.get_languages() if isinstance(lang, str)
    ]

    if not set(ocr_settings.langs).issubset(available_ocr_langs):
        match ocr_settings.quality:
            case OCRQuality.low:
                tessdata_quality = tessdata_loader.TessdataQuality.fast
            case OCRQuality.medium:
                tessdata_quality = tessdata_loader.TessdataQuality.default
            case OCRQuality.high:
                tessdata_quality = tessdata_loader.TessdataQuality.best

        for lang in ocr_settings.langs:
            tessdata_loader.load_traineddata(lang, tessdata_quality)

    if isinstance(filename, Path):
        filename = str(filename)

    md_doc = pymupdf4llm.to_markdown(
        filename,
        page_chunks=True,
        embed_images=True,
        header=False,
        footer=False,
        ocr_function=rapidtess_api.exec_ocr,
        ocr_language="+".join(ocr_settings.langs),
        show_progress=show_progress,
    )

    if isinstance(md_doc, str):
        raise ContentExtractingError

    content = models.UnstructuredContent([])

    for page in md_doc:
        text = page.get("text")
        metadata = page.get("metadata")

        if not isinstance(text, str):
            raise ContentExtractingError
        if not isinstance(metadata, dict):
            raise ContentExtractingError

        page_num = metadata.get("page_number")

        if not isinstance(page_num, int):
            raise ContentExtractingError

        page_content = extract_content_from_md_text(
            text, image_detail=image_detail
        )
        _specify_content_page(page_content, page_num)

        page_end_anchor = models.PageEndAnchor(
            start_page=page_num, end_page=page_num
        )

        if page_content.units:
            page_content.units[-1].units.append(page_end_anchor)
        else:
            page_content.units.append(models.Paragraph([page_end_anchor]))

        should_split = _should_split_on_page_boundary(page_content, content)

        if content.units and not should_split:
            first_page_unit = page_content.units.pop(0)
            content.units[-1].units.extend(first_page_unit.units)

        content.units.extend(page_content.units)

    return content
