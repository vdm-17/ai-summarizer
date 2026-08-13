"""Content extracting from markdown."""

from base64 import b64decode
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

from ai_summarizer.api import models

from .errors import ContentExtractingError


class MarkdownExtractingError(ContentExtractingError):
    """Error: unable to extract content from the given markdown document."""


def _extract_content_from_node(
    node: SyntaxTreeNode, *, image_detail: models.ImageDetail
) -> list[models.ContentBaseUnit]:
    """Extracts content from markdown syntax tree node."""

    content: list[models.ContentBaseUnit] = []

    for child_node in node.walk():
        if not child_node.is_nested:
            if child_node.type == "text":
                text = child_node.content
                if content and isinstance(content[-1], models.TextBlock):
                    content[-1].text += text
                else:
                    content.append(models.TextBlock(text))
            elif child_node.type == "image":
                src = child_node.attrs.get("src", "")
                alt = child_node.attrs.get("alt", "")

                if not isinstance(src, str):
                    raise MarkdownExtractingError
                if not isinstance(alt, str):
                    raise MarkdownExtractingError

                b64_anchor = "data:image/png;base64,"
                if not src.startswith(b64_anchor):
                    raise MarkdownExtractingError

                data = b64decode(src.replace(b64_anchor, "") + "==")
                image = models.Image(data, detail=image_detail, alt=alt)
                content.append(image)
        elif child_node.type == "inline":
            if content and isinstance(content[-1], models.TextBlock):
                content[-1].text += "\n"
            else:
                content.append(models.TextBlock("\n"))

    return content


def extract_content_from_md_text(
    text: str, *, image_detail: models.ImageDetail
) -> models.UnstructuredContent:
    """Extracts content from markdown text."""

    content = models.UnstructuredContent([])
    md_parser = MarkdownIt()

    tokens = md_parser.parse(text)
    root_node = SyntaxTreeNode(tokens)

    for node in root_node.walk():
        node_content = _extract_content_from_node(
            node, image_detail=image_detail
        )
        match node.type:
            case "heading":
                heading = models.Heading(
                    units=node_content, level=int(node.tag[1])
                )
                content.units.append(heading)
            case "paragraph":
                paragraph = models.Paragraph(node_content)
                content.units.append(paragraph)
            case _:
                pass

    return content


def extract_content_from_md(
    filename: str | Path, *, image_detail: models.ImageDetail
) -> models.UnstructuredContent:
    """Extracts content from markdown document."""

    try:
        with open(filename, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        raise MarkdownExtractingError from e

    return extract_content_from_md_text(text, image_detail=image_detail)
