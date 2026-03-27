"""Tkinter GUI for the image editing toolkit."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from .ai import generate_image
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
from .io import load_image, save_image, to_pil_image


class ImageEditorApp(tk.Tk):
    """Small image editor that previews operations inside the window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Image Generation and Processing")
        self.geometry("1100x760")
        self.configure(bg="#f3f0ea")
        self._image: Image | None = None
        self._photo = None

        self._preview = tk.Label(self, bg="#1f1f1f", width=900, height=600)
        self._preview.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=16, pady=16)

        panel = tk.Frame(self, bg="#f3f0ea")
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=16, pady=16)

        tk.Button(panel, text="Load image", command=self.load_local_image).pack(
            fill=tk.X, pady=4
        )
        tk.Button(panel, text="Generate image", command=self.generate_with_ai).pack(
            fill=tk.X, pady=4
        )
        tk.Button(panel, text="Grayscale", command=self.apply_grayscale).pack(
            fill=tk.X, pady=4
        )
        tk.Button(panel, text="Blur", command=self.apply_blur).pack(fill=tk.X, pady=4)
        tk.Button(panel, text="Resize", command=self.apply_resize).pack(fill=tk.X, pady=4)
        tk.Button(panel, text="Rotate left", command=lambda: self.apply_rotate("L")).pack(
            fill=tk.X, pady=4
        )
        tk.Button(panel, text="Rotate right", command=lambda: self.apply_rotate("R")).pack(
            fill=tk.X, pady=4
        )
        tk.Button(panel, text="Detect edges", command=self.apply_edges).pack(
            fill=tk.X, pady=4
        )
        tk.Button(panel, text="Quantize", command=self.apply_quantize).pack(
            fill=tk.X, pady=4
        )
        tk.Button(panel, text="Save as...", command=self.save_as).pack(fill=tk.X, pady=4)

        guidance = (
            "This GUI uses the same deterministic core as the CLI.\n"
            "AI generation is optional."
        )
        tk.Label(
            panel,
            text=guidance,
            justify=tk.LEFT,
            bg="#f3f0ea",
        ).pack(anchor="w", pady=(18, 0))

    def _ensure_image(self) -> bool:
        if self._image is None:
            messagebox.showinfo("No image loaded", "Load or generate an image first.")
            return False
        return True

    def _set_image(self, image: Image) -> None:
        self._image = image
        pil_image = to_pil_image(image)
        preview = pil_image.copy()
        preview.thumbnail((860, 680))
        # Use ImageTk if available for better rendering.
        try:  # pragma: no cover - depends on Pillow GUI backend availability
            from PIL import ImageTk

            self._photo = ImageTk.PhotoImage(preview, master=self)
        except Exception:
            self._photo = None
            self._preview.configure(
                image="",
                text="Preview unavailable without Pillow's GUI support",
            )
            return
        self._preview.configure(image=self._photo, text="")

    def load_local_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose an image", filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if path:
            self._set_image(load_image(path))

    def generate_with_ai(self) -> None:
        prompt = simpledialog.askstring("Generate image", "Describe the image you want:")
        if not prompt:
            return
        try:
            result = generate_image(prompt)
            if not result.image_paths:
                raise RuntimeError("No images were returned by the API.")
            self._set_image(load_image(result.image_paths[0]))
        except Exception as exc:
            messagebox.showerror("Generation failed", str(exc))

    def apply_grayscale(self) -> None:
        if self._ensure_image():
            if is_color_image(self._image):
                self._set_image(rgb_to_grayscale(self._image))
            else:
                self._set_image(self._image)

    def apply_blur(self) -> None:
        if not self._ensure_image():
            return
        size = simpledialog.askinteger("Blur", "Enter an odd blur kernel size:", minvalue=1)
        if not size:
            return
        kernel = box_blur_kernel(size)
        if is_color_image(self._image):
            channels = self._split_color_channels(self._image)
            blurred = [apply_kernel(channel, kernel) for channel in channels]
            self._set_image(combine_channels(blurred))
        else:
            self._set_image(apply_kernel(self._image, kernel))

    def apply_resize(self) -> None:
        if not self._ensure_image():
            return
        height = simpledialog.askinteger("Resize", "New height:", minvalue=1)
        width = simpledialog.askinteger("Resize", "New width:", minvalue=1)
        if not height or not width:
            return
        if is_color_image(self._image):
            channels = self._split_color_channels(self._image)
            resized = [resize_gray(channel, height, width) for channel in channels]
            self._set_image(combine_channels(resized))
        else:
            self._set_image(resize_gray(self._image, height, width))

    def apply_rotate(self, direction: str) -> None:
        if self._ensure_image():
            self._set_image(rotate_90(self._image, direction))

    def apply_edges(self) -> None:
        if not self._ensure_image():
            return
        blur_size = simpledialog.askinteger("Edges", "Blur kernel size:", minvalue=1)
        block_size = simpledialog.askinteger("Edges", "Local average block size:", minvalue=1)
        threshold = simpledialog.askfloat("Edges", "Threshold:", minvalue=0.0)
        if blur_size is None or block_size is None or threshold is None:
            return
        gray = rgb_to_grayscale(self._image) if is_color_image(self._image) else self._image
        self._set_image(detect_edges(gray, blur_size, block_size, threshold))

    def apply_quantize(self) -> None:
        if not self._ensure_image():
            return
        levels = simpledialog.askinteger("Quantize", "Number of levels:", minvalue=2)
        if not levels:
            return
        if is_color_image(self._image):
            self._set_image(quantize_color(self._image, levels))
        else:
            self._set_image(quantize_gray(self._image, levels))

    def save_as(self) -> None:
        if not self._ensure_image():
            return
        path = filedialog.asksaveasfilename(
            title="Save image",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
        )
        if path:
            saved_path = save_image(self._image, path)
            messagebox.showinfo("Saved", f"Saved to {saved_path}")

    @staticmethod
    def _split_color_channels(image: Image):
        return separate_channels(image)  # type: ignore[arg-type]


def main() -> None:
    """Launch the GUI application."""

    app = ImageEditorApp()
    app.mainloop()
