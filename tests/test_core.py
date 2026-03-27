import unittest

from image_generation_and_processing.core import (
    apply_kernel,
    box_blur_kernel,
    combine_channels,
    detect_edges,
    quantize_gray,
    resize_gray,
    rgb_to_grayscale,
    rotate_90,
    separate_channels,
)


class CoreImageTransformsTest(unittest.TestCase):
    def test_grayscale_conversion_uses_luminance_weights(self) -> None:
        image = [[[255, 0, 0], [0, 255, 0]]]

        self.assertEqual(rgb_to_grayscale(image), [[76, 150]])

    def test_channel_roundtrip_preserves_pixel_values(self) -> None:
        image = [
            [[1, 10, 100], [2, 20, 200]],
            [[3, 30, 150], [4, 40, 250]],
        ]

        self.assertEqual(combine_channels(separate_channels(image)), image)

    def test_box_blur_kernel_is_normalized(self) -> None:
        kernel = box_blur_kernel(3)

        self.assertAlmostEqual(sum(sum(row) for row in kernel), 1.0)

    def test_apply_kernel_with_identity_matrix_returns_original(self) -> None:
        image = [[10, 20], [30, 40]]
        kernel = [
            [0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0],
        ]

        self.assertEqual(apply_kernel(image, kernel), image)

    def test_resize_gray_uses_bilinear_interpolation(self) -> None:
        image = [[0, 10], [20, 30]]

        self.assertEqual(resize_gray(image, 3, 3), [[0, 5, 10], [10, 15, 20], [20, 25, 30]])

    def test_rotate_90_supports_both_directions(self) -> None:
        image = [[1, 2], [3, 4]]

        self.assertEqual(rotate_90(image, "R"), [[3, 1], [4, 2]])
        self.assertEqual(rotate_90(image, "L"), [[2, 4], [1, 3]])

    def test_quantize_gray_reduces_levels(self) -> None:
        image = [[0, 64, 128, 255]]

        self.assertEqual(quantize_gray(image, 4), [[0, 85, 170, 255]])

    def test_detect_edges_returns_binary_output(self) -> None:
        image = [[10, 10, 10], [10, 10, 10], [10, 10, 10]]

        result = detect_edges(image, 3, 3, 0.0)

        self.assertEqual(len(result), 3)
        self.assertTrue(all(pixel in {0, 255} for row in result for pixel in row))


if __name__ == "__main__":
    unittest.main()
