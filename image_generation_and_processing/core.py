"""Pure image transformation primitives.

These functions operate on in-memory image data represented as nested Python
lists so they are deterministic, easy to test, and independent of file I/O or
GUI concerns.
"""

from __future__ import annotations

from math import floor
from typing import TypeAlias

GrayImage: TypeAlias = list[list[int]]
ColorPixel: TypeAlias = list[int]
ColorImage: TypeAlias = list[list[ColorPixel]]
Image: TypeAlias = GrayImage | ColorImage
Kernel: TypeAlias = list[list[float]]


def is_color_image(image: Image) -> bool:
    """Return ``True`` when the image stores RGB pixels."""

    return bool(image and image[0] and isinstance(image[0][0], (list, tuple)))


def separate_channels(image: ColorImage) -> list[GrayImage]:
    """Split an RGB image into three grayscale channel images."""

    channel_count = len(image[0][0])
    return [
        [[int(pixel[channel]) for pixel in row] for row in image]
        for channel in range(channel_count)
    ]


def combine_channels(channels: list[GrayImage]) -> ColorImage:
    """Combine separate channel images into an RGB image."""

    height = len(channels[0])
    width = len(channels[0][0])
    return [
        [[int(channel[row][column]) for channel in channels] for column in range(width)]
        for row in range(height)
    ]


def rgb_to_grayscale(image: ColorImage) -> GrayImage:
    """Convert an RGB image to grayscale using standard luminance weights."""

    return [
        [
            round(pixel[0] * 0.299 + pixel[1] * 0.587 + pixel[2] * 0.114)
            for pixel in row
        ]
        for row in image
    ]


def box_blur_kernel(size: int) -> Kernel:
    """Return a normalized square blur kernel of ``size`` x ``size``."""

    if size <= 0:
        raise ValueError("Kernel size must be a positive integer.")
    if size % 2 == 0:
        raise ValueError("Kernel size must be odd.")
    weight = 1 / (size * size)
    return [[weight for _ in range(size)] for _ in range(size)]


def _clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(value, upper))


def _sample(image: GrayImage, row: int, column: int) -> int:
    row = _clamp(row, 0, len(image) - 1)
    column = _clamp(column, 0, len(image[0]) - 1)
    return image[row][column]


def apply_kernel(image: GrayImage, kernel: Kernel) -> GrayImage:
    """Apply a square convolution kernel to a grayscale image."""

    if not image or not image[0]:
        raise ValueError("Image must contain at least one pixel.")
    if not kernel or len(kernel) != len(kernel[0]):
        raise ValueError("Kernel must be a non-empty square matrix.")
    if len(kernel) % 2 == 0:
        raise ValueError("Kernel dimensions must be odd.")

    radius = len(kernel) // 2
    output: GrayImage = []
    for row_index in range(len(image)):
        row: list[int] = []
        for column_index in range(len(image[0])):
            total = 0.0
            for kernel_row, image_row in enumerate(
                range(row_index - radius, row_index + radius + 1)
            ):
                for kernel_column, image_column in enumerate(
                    range(column_index - radius, column_index + radius + 1)
                ):
                    total += _sample(image, image_row, image_column) * kernel[kernel_row][
                        kernel_column
                    ]
            row.append(_clamp(round(total), 0, 255))
        output.append(row)
    return output


def _bilinear_sample(image: GrayImage, row: float, column: float) -> int:
    top = floor(row)
    left = floor(column)
    bottom = _clamp(top + 1, 0, len(image) - 1)
    right = _clamp(left + 1, 0, len(image[0]) - 1)

    row_fraction = row - top
    column_fraction = column - left

    top_left = image[_clamp(top, 0, len(image) - 1)][_clamp(left, 0, len(image[0]) - 1)]
    bottom_left = image[bottom][_clamp(left, 0, len(image[0]) - 1)]
    top_right = image[_clamp(top, 0, len(image) - 1)][right]
    bottom_right = image[bottom][right]

    value = (
        top_left * (1 - row_fraction) * (1 - column_fraction)
        + bottom_left * row_fraction * (1 - column_fraction)
        + top_right * (1 - row_fraction) * column_fraction
        + bottom_right * row_fraction * column_fraction
    )
    return _clamp(round(value), 0, 255)


def resize_gray(image: GrayImage, new_height: int, new_width: int) -> GrayImage:
    """Resize a grayscale image using bilinear interpolation."""

    if new_height <= 0 or new_width <= 0:
        raise ValueError("New dimensions must be positive integers.")
    if not image or not image[0]:
        raise ValueError("Image must contain at least one pixel.")

    old_height = len(image)
    old_width = len(image[0])
    if new_height == 1 and new_width == 1:
        return [[image[0][0]]]

    output: GrayImage = []
    for row_index in range(new_height):
        row: list[int] = []
        if new_height == 1:
            source_row = 0.0
        else:
            source_row = (old_height - 1) * row_index / (new_height - 1)
        for column_index in range(new_width):
            if new_width == 1:
                source_column = 0.0
            else:
                source_column = (old_width - 1) * column_index / (new_width - 1)
            row.append(_bilinear_sample(image, source_row, source_column))
        output.append(row)
    return output


def rotate_90(image: Image, direction: str = "R") -> Image:
    """Rotate an image 90 degrees left or right."""

    if not image or not image[0]:
        return []

    if direction not in {"R", "L"}:
        raise ValueError("Direction must be 'R' or 'L'.")

    if direction == "R":
        return [list(row) for row in zip(*image[::-1])]
    return [list(row) for row in zip(*image)][::-1]


def detect_edges(image: GrayImage, blur_size: int, block_size: int, threshold: float) -> GrayImage:
    """Return a high-contrast edge map for a grayscale image."""

    blurred = apply_kernel(image, box_blur_kernel(blur_size))
    local_average = apply_kernel(blurred, box_blur_kernel(block_size))
    output: GrayImage = []
    for row_index in range(len(image)):
        row: list[int] = []
        for column_index in range(len(image[0])):
            edge_is_dark = (
                blurred[row_index][column_index]
                < local_average[row_index][column_index] - threshold
            )
            row.append(0 if edge_is_dark else 255)
        output.append(row)
    return output


def quantize_gray(image: GrayImage, levels: int) -> GrayImage:
    """Reduce the number of gray levels in an image."""

    if levels <= 1:
        raise ValueError("Quantization levels must be greater than 1.")

    output: GrayImage = []
    for row in image:
        output.append(
            [
                round(floor(pixel * (levels / 256)) * 255 / (levels - 1))
                for pixel in row
            ]
        )
    return output


def quantize_color(image: ColorImage, levels: int) -> ColorImage:
    """Reduce the number of levels in each RGB channel."""

    channels = separate_channels(image)
    quantized_channels = [quantize_gray(channel, levels) for channel in channels]
    return combine_channels(quantized_channels)
