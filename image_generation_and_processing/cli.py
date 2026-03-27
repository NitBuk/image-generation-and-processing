"""Command-line interface for loading, generating, and editing images."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path
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


def _positive_int_type(*, minimum: int = 1, odd_only: bool = False):
    def parse(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:  # pragma: no cover - argparse handles bad types
            raise argparse.ArgumentTypeError("Value must be an integer.") from exc
        if parsed < minimum:
            raise argparse.ArgumentTypeError("Value is too small.")
        if odd_only and parsed % 2 == 0:
            raise argparse.ArgumentTypeError("Value must be odd.")
        return parsed

    return parse


def _float_type(*, minimum: float = 0.0):
    def parse(value: str) -> float:
        try:
            parsed = float(value)
        except ValueError as exc:  # pragma: no cover - argparse handles bad types
            raise argparse.ArgumentTypeError("Value must be a number.") from exc
        if parsed < minimum:
            raise argparse.ArgumentTypeError("Value is too small.")
        return parsed

    return parse


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


def _apply_to_channels(
    image: Image,
    transform: Callable[[list[list[int]]], list[list[int]]],
) -> Image:
    if is_color_image(image):
        channels = [
            transform(channel) for channel in separate_channels(image)
        ]  # type: ignore[arg-type]
        return combine_channels(channels)
    return transform(image)


def transform_image(
    image: Image,
    operation: str,
    *,
    kernel_size: int | None = None,
    new_height: int | None = None,
    new_width: int | None = None,
    direction: str = "R",
    blur_size: int | None = None,
    block_size: int | None = None,
    threshold: float | None = None,
    levels: int | None = None,
) -> Image:
    """Apply a deterministic local transform to an image."""

    if operation == "grayscale":
        if is_color_image(image):
            return rgb_to_grayscale(image)
        return image
    if operation == "blur":
        if kernel_size is None:
            raise ValueError("kernel_size is required for blur.")
        kernel = box_blur_kernel(kernel_size)
        return _apply_to_channels(image, lambda channel: apply_kernel(channel, kernel))
    if operation == "resize":
        if new_height is None or new_width is None:
            raise ValueError("new_height and new_width are required for resize.")
        return _apply_to_channels(
            image,
            lambda channel: resize_gray(channel, new_height, new_width),
        )
    if operation == "rotate":
        return rotate_90(image, direction)
    if operation == "edges":
        if blur_size is None or block_size is None or threshold is None:
            raise ValueError("blur_size, block_size, and threshold are required for edges.")
        if is_color_image(image):
            image = rgb_to_grayscale(image)
        return detect_edges(image, blur_size, block_size, threshold)
    if operation == "quantize":
        if levels is None:
            raise ValueError("levels are required for quantize.")
        if is_color_image(image):
            return quantize_color(image, levels)
        return quantize_gray(image, levels)
    raise ValueError(f"Unknown transform: {operation}")


def run_transform_command(args: argparse.Namespace) -> Path:
    image = load_image(args.input_image)
    transformed = transform_image(
        image,
        args.operation,
        kernel_size=getattr(args, "kernel_size", None),
        new_height=getattr(args, "height", None),
        new_width=getattr(args, "width", None),
        direction=getattr(args, "direction", "R"),
        blur_size=getattr(args, "blur_size", None),
        block_size=getattr(args, "block_size", None),
        threshold=getattr(args, "threshold", None),
        levels=getattr(args, "levels", None),
    )
    output_path = save_image(transformed, args.output_image)
    print(f"Saved transformed image to {output_path}")
    return output_path


def _apply_operation(image: Image, choice: str) -> Image:
    if choice == "1":
        return transform_image(image, "grayscale")
    if choice == "2":
        kernel_size = _prompt_positive_int("Kernel size for blur: ", odd_only=True)
        return transform_image(image, "blur", kernel_size=kernel_size)
    if choice == "3":
        new_height = _prompt_positive_int("New height: ")
        new_width = _prompt_positive_int("New width: ")
        return transform_image(image, "resize", new_height=new_height, new_width=new_width)
    if choice == "4":
        direction = _prompt("Direction (L or R): ").upper()
        return transform_image(image, "rotate", direction=direction)
    if choice == "5":
        blur_size = _prompt_positive_int("Edge blur size: ", odd_only=True)
        block_size = _prompt_positive_int("Local average block size: ", odd_only=True)
        threshold = _prompt_float("Edge threshold: ")
        return transform_image(
            image,
            "edges",
            blur_size=blur_size,
            block_size=block_size,
            threshold=threshold,
        )
    if choice == "6":
        levels = _prompt_positive_int("Number of quantization levels: ", minimum=2)
        return transform_image(image, "quantize", levels=levels)
    if choice == "7":
        show_image(image)
        return image
    raise ValueError("Unknown option.")


def _prompt_positive_int(message: str, *, odd_only: bool = False, minimum: int = 1) -> int:
    return _positive_int_type(minimum=minimum, odd_only=odd_only)(_prompt(message))


def _prompt_float(message: str, *, minimum: float = 0.0) -> float:
    return _float_type(minimum=minimum)(_prompt(message))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image-toolkit",
        description=(
            "Edit images interactively or run deterministic local transforms from the CLI."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    transform_parser = subparsers.add_parser(
        "transform",
        help="Apply deterministic local transforms to an image.",
    )
    transform_subparsers = transform_parser.add_subparsers(dest="operation", required=True)

    def _add_resize_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--height", type=_positive_int_type(), required=True)
        parser.add_argument("--width", type=_positive_int_type(), required=True)

    def _add_rotate_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--direction",
            choices=("L", "R"),
            default="R",
            help="Rotate left or right.",
        )

    def _add_blur_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--kernel-size",
            type=_positive_int_type(odd_only=True),
            default=3,
            help="Odd kernel size used for the blur filter.",
        )

    def _add_edges_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--blur-size",
            type=_positive_int_type(odd_only=True),
            default=3,
            help="Odd blur kernel size used before edge detection.",
        )
        parser.add_argument(
            "--block-size",
            type=_positive_int_type(odd_only=True),
            default=3,
            help="Odd local-average kernel size.",
        )
        parser.add_argument(
            "--threshold",
            type=_float_type(),
            default=0.0,
            help="Difference threshold between blur and local average.",
        )

    def _add_quantize_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--levels",
            type=_positive_int_type(minimum=2),
            default=4,
            help="Number of quantization levels.",
        )

    def add_transform(
        name: str,
        help_text: str,
        *,
        extras: Callable[[argparse.ArgumentParser], None] | None = None,
    ) -> argparse.ArgumentParser:
        command_parser = transform_subparsers.add_parser(name, help=help_text)
        command_parser.add_argument("input_image", type=Path)
        command_parser.add_argument("output_image", type=Path)
        if extras is not None:
            extras(command_parser)
        command_parser.set_defaults(func=run_transform_command)
        return command_parser

    add_transform("grayscale", "Convert an image to grayscale.")
    add_transform("blur", "Apply a box blur.", extras=_add_blur_args)
    add_transform(
        "resize",
        "Resize an image using bilinear interpolation.",
        extras=_add_resize_args,
    )
    add_transform("rotate", "Rotate an image by 90 degrees.", extras=_add_rotate_args)
    add_transform("edges", "Detect edges in a grayscale image.", extras=_add_edges_args)
    add_transform("quantize", "Reduce the number of gray levels.", extras=_add_quantize_args)

    return parser


def run_from_args(args: argparse.Namespace) -> None:
    handler = getattr(args, "func", None)
    if handler is None:
        get_config()  # loads .env if present
        run_interactive()
        return
    handler(args)


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


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point for ``python -m image_generation_and_processing.cli``."""

    parser = build_parser()
    args = parser.parse_args(argv)
    run_from_args(args)


if __name__ == "__main__":  # pragma: no cover - module execution path
    main()
