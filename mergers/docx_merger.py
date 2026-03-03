"""
DOCX Merger Module
Merges multiple Word documents into a single DOCX using python-docx.
"""

import os
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from copy import deepcopy
from lxml import etree


def merge_docx(input_paths, output_path):
    """
    Merge multiple DOCX files into a single Word document.
    Inserts page breaks between documents to maintain separation.

    Args:
        input_paths (list[str]): List of absolute paths to input DOCX files.
        output_path (str): Absolute path for the merged output DOCX.

    Returns:
        str: Path to the merged output file.

    Raises:
        ValueError: If fewer than 2 files are provided.
        FileNotFoundError: If any input file does not exist.
    """
    if len(input_paths) < 2:
        raise ValueError("At least 2 DOCX files are required for merging.")

    for path in input_paths:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Input file not found: {path}")

    # Use the first document as the base
    master = Document(input_paths[0])

    for docx_path in input_paths[1:]:
        # Add a page break before appending
        master.add_page_break()

        sub_doc = Document(docx_path)

        # Copy each element from the sub document body into master
        for element in sub_doc.element.body:
            master.element.body.append(deepcopy(element))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    master.save(output_path)

    return output_path
