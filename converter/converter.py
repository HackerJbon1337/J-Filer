"""
Cross-Format Converter Module
Converts PPTX and DOCX files to PDF using Windows COM automation (comtypes).
Requires Microsoft Office installed on the machine.
"""

import os
import tempfile



def convert_to_pdf(input_path, output_dir=None):
    """
    Convert a DOCX or PPTX file to PDF using Windows COM automation.

    Args:
        input_path (str): Absolute path to the input file (.docx or .pptx).
        output_dir (str, optional): Directory for the output PDF. Defaults to temp dir.

    Returns:
        str: Absolute path to the converted PDF file.

    Raises:
        ValueError: If the file format is not supported.
        RuntimeError: If Microsoft Office is not available.
    """
    ext = os.path.splitext(input_path)[1].lower()

    if ext not in ('.docx', '.pptx', '.doc', '.ppt'):
        raise ValueError(f"Unsupported format for conversion: {ext}")

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="docmerger_")

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.pdf")

    # Ensure absolute paths for COM
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)

    try:
        if ext in ('.docx', '.doc'):
            _convert_word_to_pdf(input_path, output_path)
        elif ext in ('.pptx', '.ppt'):
            _convert_ppt_to_pdf(input_path, output_path)
    except Exception as e:
        raise RuntimeError(
            f"Failed to convert '{os.path.basename(input_path)}' to PDF. "
            f"Ensure Microsoft Office is installed. Error: {e}"
        )

    return output_path


def _convert_word_to_pdf(input_path, output_path):
    """Convert Word document to PDF using COM automation."""
    import comtypes.client
    import pythoncom

    pythoncom.CoInitialize()
    try:
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False

        doc = word.Documents.Open(input_path)
        doc.SaveAs(output_path, FileFormat=17)  # 17 = wdFormatPDF
        doc.Close()
        word.Quit()
    finally:
        pythoncom.CoUninitialize()


def _convert_ppt_to_pdf(input_path, output_path):
    """Convert PowerPoint presentation to PDF using COM automation."""
    import comtypes.client
    import pythoncom

    pythoncom.CoInitialize()
    try:
        powerpoint = comtypes.client.CreateObject('PowerPoint.Application')
        powerpoint.Visible = 1

        presentation = powerpoint.Presentations.Open(input_path, WithWindow=False)
        presentation.SaveAs(output_path, FileFormat=32)  # 32 = ppSaveAsPDF
        presentation.Close()
        powerpoint.Quit()
    finally:
        pythoncom.CoUninitialize()


def is_office_available():
    """Check if Microsoft Office COM objects are available."""
    try:
        import comtypes.client
        import pythoncom
        pythoncom.CoInitialize()
        try:
            word = comtypes.client.CreateObject('Word.Application')
            word.Quit()
            return True
        finally:
            pythoncom.CoUninitialize()
    except Exception:
        return False
