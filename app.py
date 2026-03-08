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
from converter.converter import convert_file, convert_to_pdf, is_office_available, get_supported_conversions
from converter.inverter import invert_pdf, invert_pptx
from converter.img_to_pdf import images_to_pdf as _images_to_pdf
from converter.img_to_pptx import images_to_pptx as _images_to_pptx

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


@app.route('/converter')
def converter_app():
    return render_template('converter.html')


@app.route('/inverter')
def inverter_app():
    return render_template('inverter.html')


@app.route('/compressor')
def compressor_app():
    return render_template('compressor.html')


@app.route('/app')
def merger_app():
    return render_template('index.html')


@app.route('/api/info', methods=['GET'])
def info():
    """Return system info and capabilities."""
    return jsonify({
        'office_available': is_office_available(),
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_upload_mb': 500,
        'supported_conversions': get_supported_conversions(),
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
    output_format = request.form.get('output_format', 'auto').lower().strip()

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

        # ─── Cross-format merge ────────────────────────
        elif output_format in ('pdf', 'docx', 'pptx'):
            converted_paths = []

            for path, ext, original_name in saved_paths:
                clean_ext = ext.lstrip('.')
                if clean_ext == 'doc': clean_ext = 'docx'
                if clean_ext == 'ppt': clean_ext = 'pptx'

                if clean_ext == output_format:
                    converted_paths.append(path)
                else:
                    try:
                        converted = convert_file(path, output_format, session_upload)
                        converted_paths.append(converted)
                    except Exception as e:
                        return jsonify({'error': f'Failed to convert {original_name} to {output_format.upper()}: {e}'}), 400

            out = os.path.join(session_output, f'merged.{output_format}')

            if len(converted_paths) < 2:
                shutil.copy2(converted_paths[0], out)
            else:
                if output_format == 'pdf':
                    merge_pdfs(converted_paths, out)
                elif output_format == 'docx':
                    merge_docx(converted_paths, out)
                elif output_format == 'pptx':
                    merge_pptx(converted_paths, out)

        else:
            return jsonify({
                'error': f'Cross-format merge to {output_format.upper()} is not supported.'
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


@app.route('/api/convert', methods=['POST'])
def convert():
    """
    Convert one or more files to a target format.
    Expects multipart/form-data with:
        - files[]     : one or more files (PDF, DOCX, PPTX)
        - target_format: 'pdf', 'docx', or 'pptx'
    Returns:
        - Single converted file if one input file was provided.
        - ZIP archive containing all converted files for batch requests.
    """
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files[]')
    target_format = request.form.get('target_format', '').lower().strip()

    if target_format not in ('pdf', 'docx', 'pptx'):
        return jsonify({'error': 'target_format must be pdf, docx, or pptx'}), 400

    # Create session directories
    session_id = str(uuid.uuid4())
    session_upload = os.path.join(UPLOAD_DIR, session_id)
    session_output = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_upload, exist_ok=True)
    os.makedirs(session_output, exist_ok=True)

    saved = []   # list of (saved_path, original_name)

    try:
        # ── Save uploaded files ──────────────────────────────────────
        for f in files:
            if not f.filename or not _allowed_file(f.filename):
                return jsonify({
                    'error': f'Unsupported file: {f.filename}. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
                }), 400

            ext = os.path.splitext(f.filename)[1].lower()
            safe_name = f"{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(session_upload, safe_name)
            f.save(save_path)
            saved.append((save_path, f.filename))

        # ── Convert each file ────────────────────────────────────────
        converted_paths = []   # list of (output_path, download_name)

        for save_path, original_name in saved:
            src_ext = os.path.splitext(original_name)[1].lower().lstrip('.')
            if src_ext in ('doc',):  src_ext = 'docx'
            if src_ext in ('ppt',):  src_ext = 'pptx'

            if src_ext == target_format:
                return jsonify({
                    'error': f'"{original_name}" is already a {target_format.upper()} file.'
                }), 400

            base = os.path.splitext(original_name)[0]
            out_name = f"{base}.{target_format}"

            out_path = convert_file(save_path, target_format, session_output)
            # rename to preserve original base name
            final_path = os.path.join(session_output, out_name)
            if out_path != final_path:
                if os.path.exists(final_path):
                    final_path = os.path.join(
                        session_output,
                        f"{uuid.uuid4().hex}_{out_name}"
                    )
                os.rename(out_path, final_path)

            converted_paths.append((final_path, out_name))

        # ── Return result ────────────────────────────────────────────
        if len(converted_paths) == 1:
            out_path, out_name = converted_paths[0]
            return send_file(
                out_path,
                as_attachment=True,
                download_name=out_name,
                mimetype='application/octet-stream'
            )

        # Batch: bundle into ZIP
        import zipfile
        zip_path = os.path.join(session_output, 'converted_files.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for out_path, out_name in converted_paths:
                zf.write(out_path, arcname=out_name)

        return send_file(
            zip_path,
            as_attachment=True,
            download_name='converted_files.zip',
            mimetype='application/zip'
        )

    except (ValueError, RuntimeError) as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        try:
            shutil.rmtree(session_upload, ignore_errors=True)
        except Exception:
            pass


@app.route('/api/invert', methods=['POST'])
def invert():
    """
    Invert colours of one or more PDF/PPTX files.
    Expects multipart/form-data with:
        - files[]  : one or more files (PDF, PPTX)
    Returns:
        - Single inverted file if one input file was provided.
        - ZIP archive containing all inverted files for batch requests.
    """
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files[]')
    INVERT_ALLOWED = {'.pdf', '.pptx', '.ppt'}

    session_id = str(uuid.uuid4())
    session_upload = os.path.join(UPLOAD_DIR, session_id)
    session_output = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_upload, exist_ok=True)
    os.makedirs(session_output, exist_ok=True)

    saved = []

    try:
        for f in files:
            if not f.filename:
                continue
            ext = os.path.splitext(f.filename)[1].lower()
            if ext not in INVERT_ALLOWED:
                return jsonify({
                    'error': f'Unsupported file: {f.filename}. Color inversion supports: PDF, PPTX'
                }), 400

            safe_name = f"{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(session_upload, safe_name)
            f.save(save_path)
            saved.append((save_path, f.filename, ext))

        inverted_paths = []

        for save_path, original_name, ext in saved:
            base = os.path.splitext(original_name)[0]
            norm_ext = ext if ext != '.ppt' else '.pptx'

            if norm_ext == '.pdf':
                out_name = f"{base}_inverted.pdf"
                out_path = os.path.join(session_output, out_name)
                invert_pdf(save_path, out_path)
            elif norm_ext == '.pptx':
                out_name = f"{base}_inverted.pptx"
                out_path = os.path.join(session_output, out_name)
                invert_pptx(save_path, out_path)
            else:
                continue

            inverted_paths.append((out_path, out_name))

        if len(inverted_paths) == 1:
            out_path, out_name = inverted_paths[0]
            return send_file(
                out_path,
                as_attachment=True,
                download_name=out_name,
                mimetype='application/octet-stream'
            )

        import zipfile
        zip_path = os.path.join(session_output, 'inverted_files.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for out_path, out_name in inverted_paths:
                zf.write(out_path, arcname=out_name)

        return send_file(
            zip_path,
            as_attachment=True,
            download_name='inverted_files.zip',
            mimetype='application/zip'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        try:
            shutil.rmtree(session_upload, ignore_errors=True)
        except Exception:
            pass


@app.route('/api/compress', methods=['POST'])
def compress():
    """
    Compress one or more PDF/DOCX/PPTX files.
    Expects multipart/form-data with:
        - files[]  : one or more files (PDF, DOCX, PPTX)
    Returns:
        - Single compressed file if one input file was provided.
        - ZIP archive containing all compressed files for batch requests.
    """
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files[]')
    COMPRESS_ALLOWED = {'.pdf', '.docx', '.pptx', '.doc', '.ppt'}

    session_id = str(uuid.uuid4())
    session_upload = os.path.join(UPLOAD_DIR, session_id)
    session_output = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_upload, exist_ok=True)
    os.makedirs(session_output, exist_ok=True)

    saved = []

    try:
        for f in files:
            if not f.filename:
                continue
            ext = os.path.splitext(f.filename)[1].lower()
            if ext not in COMPRESS_ALLOWED:
                return jsonify({
                    'error': f'Unsupported file: {f.filename}. Compression supports: PDF, DOCX, PPTX'
                }), 400

            safe_name = f"{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(session_upload, safe_name)
            f.save(save_path)
            saved.append((save_path, f.filename, ext))

        compressed_paths = []

        for save_path, original_name, ext in saved:
            base = os.path.splitext(original_name)[0]
            norm_ext = ext.lstrip('.')
            if norm_ext == 'doc': norm_ext = 'docx'
            if norm_ext == 'ppt': norm_ext = 'pptx'

            out_name = f"{base}_compressed.{norm_ext}"
            out_path = os.path.join(session_output, out_name)

            try:
                if norm_ext == 'pdf':
                    _compress_pdf(save_path, out_path)
                elif norm_ext in ('docx', 'pptx'):
                    _compress_office(save_path, out_path)
                else:
                    continue
            except Exception:
                # If compression fails, copy original
                shutil.copy2(save_path, out_path)

            compressed_paths.append((out_path, out_name))

        if len(compressed_paths) == 1:
            out_path, out_name = compressed_paths[0]
            return send_file(
                out_path,
                as_attachment=True,
                download_name=out_name,
                mimetype='application/octet-stream'
            )

        import zipfile
        zip_path = os.path.join(session_output, 'compressed_files.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for out_path, out_name in compressed_paths:
                zf.write(out_path, arcname=out_name)

        return send_file(
            zip_path,
            as_attachment=True,
            download_name='compressed_files.zip',
            mimetype='application/zip'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        try:
            shutil.rmtree(session_upload, ignore_errors=True)
        except Exception:
            pass


@app.route('/api/images-to-pdf', methods=['POST'])
def images_to_pdf():
    """
    Convert one or more image files (JPG, PNG, WEBP, BMP, TIFF, GIF)
    into a single merged PDF. Images are placed in upload order.
    Expects multipart/form-data with:
        - files[]  : one or more image files
    Returns:
        - A single PDF named 'images.pdf'
    """
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files[]')
    IMAGE_ALLOWED = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif', '.gif'}

    session_id = str(uuid.uuid4())
    session_upload = os.path.join(UPLOAD_DIR, session_id)
    session_output = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_upload, exist_ok=True)
    os.makedirs(session_output, exist_ok=True)

    saved_paths = []

    try:
        for f in files:
            if not f.filename:
                continue
            ext = os.path.splitext(f.filename)[1].lower()
            if ext not in IMAGE_ALLOWED:
                return jsonify({
                    'error': f'Unsupported file: {f.filename}. Supported: JPG, PNG, WEBP, BMP, TIFF, GIF'
                }), 400
            safe_name = f"{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(session_upload, safe_name)
            f.save(save_path)
            saved_paths.append(save_path)

        if not saved_paths:
            return jsonify({'error': 'No valid image files found'}), 400

        out_path = os.path.join(session_output, 'images.pdf')
        _images_to_pdf(saved_paths, out_path)

        return send_file(
            out_path,
            as_attachment=True,
            download_name='images.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        try:
            shutil.rmtree(session_upload, ignore_errors=True)
        except Exception:
            pass


@app.route('/api/images-to-pptx', methods=['POST'])
def images_to_pptx():
    """
    Convert one or more image files (JPG, PNG, WEBP, etc.)
    into a single PPTX. Images are placed in upload order.
    Expects multipart/form-data with:
        - files[]  : one or more image files
    Returns:
        - A single PPTX named 'images.pptx'
    """
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files[]')
    IMAGE_ALLOWED = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif', '.gif'}

    session_id = str(uuid.uuid4())
    session_upload = os.path.join(UPLOAD_DIR, session_id)
    session_output = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_upload, exist_ok=True)
    os.makedirs(session_output, exist_ok=True)

    saved_paths = []

    try:
        for f in files:
            if not f.filename:
                continue
            ext = os.path.splitext(f.filename)[1].lower()
            if ext not in IMAGE_ALLOWED:
                return jsonify({
                    'error': f'Unsupported file: {f.filename}. Supported: JPG, PNG, WEBP, BMP, TIFF, GIF'
                }), 400
            safe_name = f"{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(session_upload, safe_name)
            f.save(save_path)
            saved_paths.append(save_path)

        if not saved_paths:
            return jsonify({'error': 'No valid image files found'}), 400

        out_path = os.path.join(session_output, 'images.pptx')
        _images_to_pptx(saved_paths, out_path)

        return send_file(
            out_path,
            as_attachment=True,
            download_name='images.pptx',
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        try:
            shutil.rmtree(session_upload, ignore_errors=True)
        except Exception:
            pass


# ─── Compression Helpers ──────────────────────────────────────
def _compress_pdf(input_path, output_path):
    """Compress a PDF by downscaling embedded images and optimizing streams."""
    try:
        import fitz
        from PIL import Image
        from io import BytesIO

        doc = fitz.open(input_path)
        
        max_dim = 1200
        jpeg_quality = 50
        
        # Iterate over all pages and images to downsample and compress
        for page in doc:
            for img in page.get_images(full=True):
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    pil_img = Image.open(BytesIO(image_bytes))
                    
                    # Downscale large images
                    if pil_img.width > max_dim or pil_img.height > max_dim:
                        pil_img.thumbnail((max_dim, max_dim), Image.LANCZOS)
                        
                    # Convert to RGB to safely save as JPEG
                    if pil_img.mode in ('RGBA', 'P', 'LA'):
                        pil_img = pil_img.convert('RGB')
                        
                    buf = BytesIO()
                    pil_img.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
                    new_image_bytes = buf.getvalue()
                    
                    # Only replace image if compression actually reduced the byte size
                    if len(new_image_bytes) < len(image_bytes):
                        page.replace_image(xref, stream=new_image_bytes)
                except Exception:
                    pass  # Keep original if processing fails
                    
        # Save with maximal garbage collection and stream compression
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()
    except Exception as e:
        # Fallback to pikepdf lossless compression if fitz manipulations fail
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
    MAX_DIM = 1200  # Max width/height in pixels
    JPEG_QUALITY = 50

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
                        # Only use compressed version if it is smaller
                        if len(buf.getvalue()) < len(data):
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
