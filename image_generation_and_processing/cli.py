"""Command-line interface for loading, generating, and editing images."""

from __future__ import annotations

from textwrap import dedent

from .ai import generate_image
from .config import get_config
from .core import (
    Image,
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


def _prompt(message: str) -> str:
    return input(message).strip()


def _prompt_positive_int(message: str, *, odd_only: bool = False, minimum: int = 1) -> int:
    value = int(_prompt(message))
    if value < minimum:
        raise ValueError("Value is too small.")
    if odd_only and value % 2 == 0:
        raise ValueError("Value must be odd.")
    return value


def _prompt_float(message: str, *, minimum: float = 0.0) -> float:
    value = float(_prompt(message))
    if value < minimum:
        raise ValueError("Value is too small.")
    return value


def _load_initial_image() -> Image:
    while True:
        choice = _prompt(
            "Enter 1 to generate an image with AI or 2 to load a local image: "
        )
        if choice == "1":
            prompt = _prompt("Describe the image you want to generate: ")
            result = generate_image(prompt)
            if not result.image_paths:
                raise RuntimeError("The API did not return any images.")
            return load_image(result.image_paths[0])
        if choice == "2":
            image_path = _prompt("Enter the path to an image file: ")
            return load_image(image_path)
        print("Invalid option. Please enter 1 or 2.")


def _apply_operation(image: Image, choice: str) -> Image:
    if choice == "1":
        if is_color_image(image):
            return rgb_to_grayscale(image)
        print("The image is already grayscale.")
        return image
    if choice == "2":
        kernel_size = _prompt_positive_int("Kernel size for blur: ", odd_only=True)
        kernel = box_blur_kernel(kernel_size)
        if is_color_image(image):
            channels = []
            for channel in separate_channels(image):  # type: ignore[arg-type]
                channels.append(apply_kernel(channel, kernel))
            return combine_channels(channels)
        return apply_kernel(image, kernel)
    if choice == "3":
        new_height = _prompt_positive_int("New height: ")
        new_width = _prompt_positive_int("New width: ")
        if is_color_image(image):
            channels = []
            for channel in separate_channels(image):  # type: ignore[arg-type]
                channels.append(resize_gray(channel, new_height, new_width))
            return combine_channels(channels)
        return resize_gray(image, new_height, new_width)
    if choice == "4":
        direction = _prompt("Direction (L or R): ").upper()
        return rotate_90(image, direction)
    if choice == "5":
        blur_size = _prompt_positive_int("Edge blur size: ", odd_only=True)
        block_size = _prompt_positive_int("Local average block size: ", odd_only=True)
        threshold = _prompt_float("Edge threshold: ")
        if is_color_image(image):
            image = rgb_to_grayscale(image)
        return detect_edges(image, blur_size, block_size, threshold)
    if choice == "6":
        levels = _prompt_positive_int("Number of quantization levels: ", minimum=2)
        if is_color_image(image):
            return quantize_color(image, levels)
        return quantize_gray(image, levels)
    if choice == "7":
        show_image(image)
        return image
    raise ValueError("Unknown option.")


def run_interactive() -> None:
    """Run the interactive image editing flow."""

    image = _load_initial_image()
    menu = dedent(
        """
        Choose an action:
        1. Convert RGB image to grayscale
        2. Blur the image
        3. Resize the image
        4. Rotate the image by 90 degrees
        5. Detect edges
        6. Quantize the image
        7. Show the image
        8. Save and exit
        """
    ).strip()

    while True:
        choice = _prompt(f"{menu}\nYour choice: ")
        if choice == "8":
            break
        try:
            image = _apply_operation(image, choice)
        except Exception as exc:
            print(f"Could not apply operation: {exc}")

    save_choice = _prompt("Enter 1 to save the result or 2 to quit without saving: ")
    if save_choice == "1":
        output_name = _prompt("Enter the output file name: ")
        saved_path = save_image(image, output_name)
        print(f"Saved to {saved_path}")


def main() -> None:
    """Entry point for ``python -m image_generation_and_processing.cli``."""

    get_config()  # loads .env if present
    run_interactive()


if __name__ == "__main__":  # pragma: no cover - module execution path
    main()
