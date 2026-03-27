"""File I/O helpers for loading, displaying, and saving images."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .core import Image, is_color_image

RGB_MODE = "RGB"
GRAY_MODE = "L"


def _require_pillow() -> Any:
    try:
        from PIL import Image as PILImage  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local environment
        raise RuntimeError(
            "Pillow is required for image file I/O. Install the project with `pip install -e .`."
        ) from exc
    return PILImage


def _reshape_pixels(pixels: list[Any], width: int, height: int) -> list[list[Any]]:
    return [pixels[index * width : (index + 1) * width] for index in range(height)]


def _to_list_image(image: Any) -> Image:
    width, height = image.size
    pixels = _reshape_pixels(list(image.getdata()), width, height)
    if pixels and pixels[0] and isinstance(pixels[0][0], tuple):
        return [[list(pixel) for pixel in row] for row in pixels]
    return [[int(pixel) for pixel in row] for row in pixels]


def load_image(image_filename: str | Path, mode: str = RGB_MODE) -> Image:
    """Load an image file into nested lists."""

    PILImage = _require_pillow()
    image = PILImage.open(image_filename).convert(mode)
    return _to_list_image(image)


def _to_pil_image(image: Image) -> Any:
    PILImage = _require_pillow()
    image_copy = deepcopy(image)
    if is_color_image(image_copy):
        height = len(image_copy)
        width = len(image_copy[0])
        pil_image = PILImage.new(RGB_MODE, (width, height))
        flat_pixels = [tuple(pixel) for row in image_copy for pixel in row]
        pil_image.putdata(flat_pixels)
        return pil_image

    height = len(image_copy)
    width = len(image_copy[0])
    pil_image = PILImage.new(GRAY_MODE, (width, height))
    flat_pixels = [int(pixel) for row in image_copy for pixel in row]
    pil_image.putdata(flat_pixels)
    return pil_image


def show_image(image: Image) -> None:
    """Open the image using the default image viewer."""

    _to_pil_image(image).show()


def save_image(image: Image, filename: str | Path) -> Path:
    """Save an image to disk and return the final file path."""

    path = Path(filename)
    if path.suffix.lower() != ".png":
        path = path.with_suffix(".png")
    _to_pil_image(image).save(path)
    return path


def to_pil_image(image: Image) -> Any:
    """Expose a PIL image for GUI preview rendering."""

    return _to_pil_image(image)
