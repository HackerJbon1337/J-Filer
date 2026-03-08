"""
Color Inverter Module
Inverts all colors in PDF and PPTX files — ideal for printing
dark-background lecture slides on white paper.

Uses PyMuPDF (fitz) for PDF rasterisation and Pillow for pixel-level
color inversion. PPTX is handled via a PPTX→PDF→invert→PPTX pipeline.
"""

import os
import io
import tempfile


def invert_pdf(input_path, output_path):
    """
    Invert all colours in a PDF document.

    Each page is rasterised at 200 DPI, pixel-inverted using
    Pillow ImageOps.invert, then reassembled into a clean PDF
    via PyMuPDF.

    Args:
        input_path  (str): Path to the source PDF.
        output_path (str): Path to write the inverted PDF.
    """
    import fitz  # PyMuPDF
    from PIL import Image, ImageOps

    DPI = 200
    zoom = DPI / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    src = fitz.open(input_path)
    dst = fitz.open()  # new empty PDF

    for page in src:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data)).convert("RGB")

        # Invert colours
        inverted = ImageOps.invert(img)

        # Write inverted image to bytes
        buf = io.BytesIO()
        inverted.save(buf, format="PNG")
        buf.seek(0)

        # Insert as a new page in destination PDF with original page dimensions
        new_page = dst.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, stream=buf.getvalue())

    dst.save(output_path, deflate=True)
    dst.close()
    src.close()


def invert_pptx(input_path, output_path):
    """
    Invert all colours in a PPTX presentation.

    Pipeline: PPTX → PDF (via COM) → invert PDF → PDF → PPTX (image slides).
    This guarantees pixel-perfect inversion of every element including
    embedded images, gradients, and complex shapes.

    Args:
        input_path  (str): Path to the source PPTX.
        output_path (str): Path to write the inverted PPTX.
    """
    from converter.converter import _pptx_to_pdf, _pdf_to_pptx

    tmp_dir = tempfile.mkdtemp(prefix='jfiler_invert_')
    pdf_path = os.path.join(tmp_dir, 'original.pdf')
    inverted_pdf = os.path.join(tmp_dir, 'inverted.pdf')

    # Step 1: PPTX → PDF
    _pptx_to_pdf(os.path.abspath(input_path), os.path.abspath(pdf_path))

    # Step 2: Invert the PDF
    invert_pdf(pdf_path, inverted_pdf)

    # Step 3: Inverted PDF → PPTX
    _pdf_to_pptx(inverted_pdf, os.path.abspath(output_path))
