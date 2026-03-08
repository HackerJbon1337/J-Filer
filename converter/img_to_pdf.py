"""
Image → PDF Converter
Converts one or more image files (JPG, PNG, WEBP, BMP, TIFF, GIF)
into a single merged PDF document.

Each image becomes one page in the output PDF. Images are scaled to
fit an A4 page at 150 DPI while preserving their aspect ratio.
No Microsoft Office required — pure Pillow + fpdf2 / reportlab path.
Falls back to a simple Pillow multi-page save if fpdf2 not present.
"""

import os
from PIL import Image


# A4 at 150 DPI
A4_W_PX = 1240   # ~210mm
A4_H_PX = 1754   # ~297mm


def _fit_image(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    """Return a copy of img scaled to fit within max_w × max_h (preserving ratio)."""
    img = img.convert('RGB')
    iw, ih = img.size
    scale = min(max_w / iw, max_h / ih, 1.0)   # never upscale
    if scale < 1.0:
        new_w = int(iw * scale)
        new_h = int(ih * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    return img


def _place_on_white_canvas(img: Image.Image, cw: int, ch: int) -> Image.Image:
    """Center img on a white canvas of size cw × ch."""
    canvas = Image.new('RGB', (cw, ch), (255, 255, 255))
    x = (cw - img.width)  // 2
    y = (ch - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def images_to_pdf(image_paths: list[str], output_path: str) -> None:
    """
    Merge one or more image files into a single PDF.

    Args:
        image_paths  (list[str]): Ordered list of absolute paths to image files.
        output_path  (str):       Destination path for the output PDF.
    """
    if not image_paths:
        raise ValueError("No images provided.")

    pages: list[Image.Image] = []

    for path in image_paths:
        img = Image.open(path)
        img = _fit_image(img, A4_W_PX, A4_H_PX)
        page = _place_on_white_canvas(img, A4_W_PX, A4_H_PX)
        pages.append(page)

    first, *rest = pages
    first.save(
        output_path,
        format='PDF',
        save_all=True,
        append_images=rest,
        resolution=150,
    )
