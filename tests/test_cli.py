from __future__ import annotations

import importlib.util
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from image_generation_and_processing.cli import (
    build_parser,
    run_transform_command,
    transform_image,
)
from image_generation_and_processing.io import load_image, save_image

PIL_AVAILABLE = importlib.util.find_spec("PIL") is not None


class CliTransformTests(unittest.TestCase):
    def test_parser_recognizes_transform_subcommands(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "transform",
                "resize",
                "input.png",
                "output.png",
                "--height",
                "2",
                "--width",
                "3",
            ]
        )

        self.assertEqual(args.command, "transform")
        self.assertEqual(args.operation, "resize")
        self.assertEqual(args.height, 2)
        self.assertEqual(args.width, 3)

    def test_transform_image_blurs_each_color_channel(self) -> None:
        image = [[[1, 10, 100], [2, 20, 200]]]

        self.assertEqual(transform_image(image, "blur", kernel_size=1), image)

    @unittest.skipUnless(PIL_AVAILABLE, "Pillow is required for the file-backed CLI test.")
    def test_transform_command_writes_grayscale_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_dir = Path(tmp_dir)
            input_path = temp_dir / "input.png"
            output_path = temp_dir / "output"
            save_image([[[255, 0, 0], [0, 255, 0]]], input_path)

            result_path = run_transform_command(
                Namespace(
                    operation="grayscale",
                    input_image=input_path,
                    output_image=output_path,
                )
            )

            self.assertEqual(result_path.suffix, ".png")
            self.assertTrue(result_path.exists())
            self.assertEqual(load_image(result_path, mode="L"), [[76, 150]])


if __name__ == "__main__":
    unittest.main()
