"""Counting tokens of image content."""

from io import BytesIO
from math import ceil, floor, sqrt

from PIL import Image

from ai_summarizer.api.models import ImageDetail

from .errors import TokensCountingError

# Tile-based:
# low  -> fixed base tokens
# high -> base_tokens + (tile_count * tile_tokens)
_TILE_BASED_LLM_MODEL_CONFIGS: dict[str, tuple[int, int]] = {
    "gpt-5": (70, 140),
    "gpt-5-codex": (70, 140),
    "gpt-5.1": (70, 140),
    "gpt-5-chat-latest": (70, 140),
    "gpt-4o": (85, 170),
    "gpt-4o-2024-05-13": (85, 170),
    "gpt-4.1": (85, 170),
    "gpt-4.5": (85, 170),
    "gpt-4.5-preview": (85, 170),
    "gpt-4o-mini": (2833, 5667),
    "o1": (75, 150),
    "o1-pro": (75, 150),
    "o3": (75, 150),
    "o3-deep-research": (75, 150),
    "o3-pro-2025-06-10": (75, 150),
    "computer-use-preview": (65, 129),
}

# Patch-based:
# tokens = resized_patch_count * multiplier
_PATCH_BASED_LLM_MODEL_CONFIGS: dict[str, float] = {
    "gpt-5.4-mini": 1.62,
    "gpt-5.4-nano": 2.46,
    "gpt-5.2": 1.2,
    "gpt-5-mini": 1.62,
    "gpt-5-nano": 2.46,
    "o4-mini": 1.72,
    "o4-mini-deep-research": 1.72,
    "gpt-4.1-mini": 1.62,
    "gpt-4.1-nano": 2.46,
    "codex-mini-latest": 1.72,
}


class ImageTokensCountingError(TokensCountingError):
    """Error: unable to count tokens of the given image content."""


class WidthValueError(ImageTokensCountingError):
    """Width value error."""

    def __init__(self, value: int) -> None:
        message = (
            f"Error: {value} is invalid width value."
            "Width must be positive integer."
        )
        super().__init__(message)


class HeightValueError(ImageTokensCountingError):
    """Height value error."""

    def __init__(self, value: int) -> None:
        message = (
            f"Error: {value} is invalid height value."
            "Height must be positive integer."
        )
        super().__init__(message)


def _fit_inside(
    width: int, height: int, max_dimension: int
) -> tuple[int, int]:
    """Encloses the image in a max_dimension x max_dimension square."""

    if max(width, height) <= max_dimension:
        return width, height

    scale = max_dimension / max(width, height)
    return max(1, floor(width * scale)), max(1, floor(height * scale))


def _scale_short_side_to(
    width: int, height: int, target_short_side: int
) -> tuple[int, int]:
    """Scales so that the short side becomes target_short_side."""

    short_side = min(width, height)

    scale = target_short_side / short_side
    return max(1, floor(width * scale)), max(1, floor(height * scale))


def _count_tile_based_tokens(
    width: int,
    height: int,
    *,
    base_tokens: int,
    tile_tokens: int,
    detail: ImageDetail,
) -> int:
    """Roughly estimates image tokens count for tile-based models."""

    if detail == "low":
        return base_tokens

    # For a rough estimate, used the value auto ~= high.
    resized_w, resized_h = _fit_inside(width, height, 2048)
    resized_w, resized_h = _scale_short_side_to(resized_w, resized_h, 768)

    tiles_w = ceil(resized_w / 512)
    tiles_h = ceil(resized_h / 512)
    tile_count = tiles_w * tiles_h

    return base_tokens + (tile_count * tile_tokens)


def _count_patch_based_tokens(
    width: int,
    height: int,
    *,
    patch_budget: int,
    multiplier: float,
) -> int:
    """Roughly estimates image tokens count for patch-based models."""

    # Counting the number of patches of the original image
    original_patch_count = ceil(width / 32) * ceil(height / 32)

    if original_patch_count <= patch_budget and max(width, height) <= 2048:
        resized_patch_count = original_patch_count
    else:
        # Docs limitation: both patch budget and max dimension 2048
        scale_by_budget = sqrt((32 * 32 * patch_budget) / (width * height))
        scale_by_dimension = 2048 / max(width, height)
        shrink_factor = min(scale_by_budget, scale_by_dimension, 1.0)

        raw_w = width * shrink_factor
        raw_h = height * shrink_factor

        adjusted_shrink_factor = shrink_factor * min(
            floor(raw_w / 32) / (raw_w / 32) if raw_w >= 32 else 1.0,
            floor(raw_h / 32) / (raw_h / 32) if raw_h >= 32 else 1.0,
        )

        resized_w = max(1, floor(width * adjusted_shrink_factor))
        resized_h = max(1, floor(height * adjusted_shrink_factor))

        if max(resized_w, resized_h) > 2048:
            resized_w, resized_h = _fit_inside(resized_w, resized_h, 2048)

        resized_patch_count = ceil(resized_w / 32) * ceil(resized_h / 32)

        # Safety net against exceeding the budget due to rounding
        while resized_patch_count > patch_budget:
            if resized_w >= resized_h and resized_w > 1:
                resized_w -= 1
            elif resized_h > 1:
                resized_h -= 1
            else:
                break
            resized_patch_count = ceil(resized_w / 32) * ceil(resized_h / 32)

    return int(ceil(resized_patch_count * multiplier))


def count_image_tokens(
    data: bytes,
    llm_model: str,
    *,
    detail: ImageDetail,
) -> int:
    """Roughly estimates image tokens count for OpenAI model."""

    image = Image.open(BytesIO(data))

    if image.width <= 0:
        raise WidthValueError(image.width)
    if image.height <= 0:
        raise HeightValueError(image.height)

    if llm_model in _TILE_BASED_LLM_MODEL_CONFIGS:
        base_tokens, tile_tokens = _TILE_BASED_LLM_MODEL_CONFIGS[llm_model]
        return _count_tile_based_tokens(
            image.width,
            image.height,
            detail=detail,
            base_tokens=base_tokens,
            tile_tokens=tile_tokens,
        )

    if llm_model not in _PATCH_BASED_LLM_MODEL_CONFIGS:
        return 0

    patch_budget = 1536
    multiplier = _PATCH_BASED_LLM_MODEL_CONFIGS[llm_model]

    return _count_patch_based_tokens(
        image.width,
        image.height,
        patch_budget=patch_budget,
        multiplier=multiplier,
    )
