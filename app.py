"""
Universal Document Merger — Main Application
Flask backend + pywebview native desktop window.
"""

import os
import sys
import uuid
import shutil
import tempfile
import threading
from flask import Flask, request, jsonify, send_file, render_template

# ─── Path resolution for PyInstaller bundled .exe ─────────────
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    BASE_DIR = sys._MEIPASS
else:
    # Running as a normal Python script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add project root to path
sys.path.insert(0, BASE_DIR)

from mergers.pdf_merger import merge_pdfs
from mergers.docx_merger import merge_docx
from mergers.pptx_merger import merge_pptx
from converter.converter import convert_to_pdf, is_office_available

# ─── Flask App ────────────────────────────────────────────────
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), 'docmerger_uploads')
OUTPUT_DIR = os.path.join(tempfile.gettempdir(), 'docmerger_output')

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.pptx', '.doc', '.ppt'}


def _allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/app')
def merger_app():
    return render_template('index.html')


@app.route('/api/info', methods=['GET'])
def info():
    """Return system info and capabilities."""
    return jsonify({
        'office_available': is_office_available(),
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_upload_mb': 500
    })


@app.after_request
def add_header(r):
    """Disable caching for development to ensure UI updates are visible."""
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route('/api/merge', methods=['POST'])
def merge():
    """
    Merge uploaded files.
    Expects multipart/form-data with:
        - files[]: multiple files
        - output_format: 'pdf', 'docx', 'pptx', or 'auto'
    """
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files[]')
    output_format = request.form.get('output_format', 'auto').lower()

    if len(files) < 2:
        return jsonify({'error': 'At least 2 files are required for merging'}), 400

    # Create session directories
    session_id = str(uuid.uuid4())
    session_upload = os.path.join(UPLOAD_DIR, session_id)
    session_output = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_upload, exist_ok=True)
    os.makedirs(session_output, exist_ok=True)

    saved_paths = []
    file_types = set()

    try:
        # Save uploaded files
        for f in files:
            if not f.filename or not _allowed_file(f.filename):
                return jsonify({
                    'error': f'Unsupported file: {f.filename}. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
                }), 400

            ext = os.path.splitext(f.filename)[1].lower()
            safe_name = f"{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(session_upload, safe_name)
            f.save(save_path)
            saved_paths.append((save_path, ext, f.filename))
            file_types.add(ext.replace('.', ''))

        # Normalize types
        normalized_types = set()
        for t in file_types:
            if t in ('doc', 'docx'):
                normalized_types.add('docx')
            elif t in ('ppt', 'pptx'):
                normalized_types.add('pptx')
            else:
                normalized_types.add(t)

        # Determine output format
        if output_format == 'auto':
            if len(normalized_types) == 1:
                output_format = normalized_types.pop()
            else:
                output_format = 'pdf'

        # ─── Same-format merge ─────────────────────────
        if len(normalized_types) == 1 and output_format in normalized_types:
            fmt = normalized_types.pop() if normalized_types else output_format
            paths = [p[0] for p in saved_paths]

            if fmt == 'pdf':
                out = os.path.join(session_output, 'merged.pdf')
                merge_pdfs(paths, out)
            elif fmt == 'docx':
                out = os.path.join(session_output, 'merged.docx')
                merge_docx(paths, out)
            elif fmt == 'pptx':
                out = os.path.join(session_output, 'merged.pptx')
                merge_pptx(paths, out)
            else:
                return jsonify({'error': f'Unsupported output format: {fmt}'}), 400

        # ─── Cross-format merge → PDF ──────────────────
        elif output_format == 'pdf':
            pdf_paths = []

            for path, ext, original_name in saved_paths:
                if ext == '.pdf':
                    pdf_paths.append(path)
                elif ext in ('.docx', '.doc', '.pptx', '.ppt'):
                    converted = convert_to_pdf(path, session_upload)
                    pdf_paths.append(converted)

            if len(pdf_paths) < 2:
                # If only one file converted, just return it
                out = os.path.join(session_output, 'merged.pdf')
                shutil.copy2(pdf_paths[0], out)
            else:
                out = os.path.join(session_output, 'merged.pdf')
                merge_pdfs(pdf_paths, out)

        else:
            return jsonify({
                'error': f'Cross-format merge to {output_format.upper()} is not supported. '
                         f'Use PDF as the output format for mixed-format merging.'
            }), 400

        # ─── Compress file size if requested ──────────
        compress = request.form.get('compress', '0') == '1'

        if compress:
            compressed_path = os.path.join(session_output, f'compressed.{output_format}')
            try:
                if output_format == 'pdf':
                    _compress_pdf(out, compressed_path)
                elif output_format in ('docx', 'pptx'):
                    _compress_office(out, compressed_path)
                else:
                    compressed_path = out  # no compression available

                if os.path.exists(compressed_path) and compressed_path != out:
                    out = compressed_path
            except Exception:
                pass  # If compression fails, return the uncompressed file

        # Return the merged file
        return send_file(
            out,
            as_attachment=True,
            download_name=f'merged.{output_format}',
            mimetype='application/octet-stream'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup uploaded files (output kept for potential re-download)
        try:
            shutil.rmtree(session_upload, ignore_errors=True)
        except Exception:
            pass


# ─── Compression Helpers ──────────────────────────────────────
def _compress_pdf(input_path, output_path):
    """Compress a PDF by rewriting with compressed streams."""
    import pikepdf
    with pikepdf.open(input_path) as pdf:
        pdf.save(output_path,
                 compress_streams=True,
                 object_stream_mode=pikepdf.ObjectStreamMode.generate,
                 recompress_flate=True,
                 linearize=True)


def _compress_office(input_path, output_path):
    """Compress a DOCX/PPTX by re-compressing embedded images."""
    import zipfile
    from io import BytesIO

    try:
        from PIL import Image
        has_pillow = True
    except ImportError:
        has_pillow = False

    IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
    MAX_DIM = 1920  # Max width/height in pixels
    JPEG_QUALITY = 72

    with zipfile.ZipFile(input_path, 'r') as zin:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED,
                             compresslevel=9) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                ext = os.path.splitext(item.filename)[1].lower()

                if has_pillow and ext in IMAGE_EXTS:
                    try:
                        img = Image.open(BytesIO(data))
                        # Downscale large images
                        if img.width > MAX_DIM or img.height > MAX_DIM:
                            img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
                        buf = BytesIO()
                        # Convert to RGB for JPEG output
                        if img.mode in ('RGBA', 'P', 'LA'):
                            img = img.convert('RGB')
                        img.save(buf, format='JPEG', quality=JPEG_QUALITY,
                                 optimize=True)
                        data = buf.getvalue()
                        # Update the filename extension to .jpeg
                        # (keeping original to avoid broken references)
                    except Exception:
                        pass  # Keep original image data on error

                zout.writestr(item, data)


# ─── Desktop App Launcher ─────────────────────────────────────
def main():
    """Launch the application — opens in the default browser."""
    import webbrowser
    import time

    host = '127.0.0.1'
    port = 5000
    url = f'http://{host}:{port}'

    # Open the browser after a short delay to let Flask start
    def open_browser():
        time.sleep(1.2)
        webbrowser.open(url)

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    print("=" * 48)
    print("  Universal Document Merger")
    print(f"  Running at: {url}")
    print("  Press Ctrl+C to stop")
    print("=" * 48)

    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
