"""Top-level package for the image generation and processing toolkit."""

from .core import (
    apply_kernel,
    box_blur_kernel,
    combine_channels,
    detect_edges,
    is_color_image,
    quantize_color,
    quantize_gray,
    resize_gray,
    rgb_to_grayscale,
    rotate_90,
    separate_channels,
)
from .io import load_image, save_image, show_image

__all__ = [
    "apply_kernel",
    "box_blur_kernel",
    "combine_channels",
    "detect_edges",
    "is_color_image",
    "load_image",
    "quantize_color",
    "quantize_gray",
    "resize_gray",
    "rgb_to_grayscale",
    "rotate_90",
    "save_image",
    "separate_channels",
    "show_image",
]
