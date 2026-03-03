"""
PDF Merger Module
Merges multiple PDF files into a single PDF using PyPDF2.
"""

import os
from PyPDF2 import PdfMerger


def merge_pdfs(input_paths, output_path):
    """
    Merge multiple PDF files into a single PDF.

    Args:
        input_paths (list[str]): List of absolute paths to input PDF files.
        output_path (str): Absolute path for the merged output PDF.

    Returns:
        str: Path to the merged output file.

    Raises:
        ValueError: If fewer than 2 files are provided.
        FileNotFoundError: If any input file does not exist.
    """
    if len(input_paths) < 2:
        raise ValueError("At least 2 PDF files are required for merging.")

    for path in input_paths:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Input file not found: {path}")

    merger = PdfMerger()

    try:
        for pdf_path in input_paths:
            merger.append(pdf_path)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        merger.write(output_path)
    finally:
        merger.close()

    return output_path
