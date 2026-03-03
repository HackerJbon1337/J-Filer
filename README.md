# J-Filer — Universal Document Merger

A high-performance, offline desktop application for merging and consolidating **PPTX**, **DOCX**, and **PDF** files into a single structured output — with built-in **file size compression**.

Built with Python, Flask, and a stunning **Liquid Glass** UI — runs entirely offline.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square)
[![Download Latest Release](https://img.shields.io/badge/Download-Latest_Release-ff69b4?style=flat-square&logo=github)](https://github.com/HackerJbon1337/J-Filer/releases/latest)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **PDF Merge** | Combine multiple PDFs into one |
| **DOCX Merge** | Merge Word documents with page breaks |
| **PPTX Merge** | Concatenate PowerPoint slides |
| **Cross-Format** | Mix PPTX + DOCX + PDF → unified PDF |
| **Compress Output** | Reduce merged file size — PDF stream compression via `pikepdf`, image compression for DOCX/PPTX via `Pillow` |
| **Drag & Drop** | Beautiful file upload with drag-and-drop |
| **Progress Bar** | Real-time percentage during merge |
| **Offline** | 100% local — no internet required |
| **Liquid Glass UI** | Premium dark theme with iridescent effects |

---

## 🚀 Installation

### Option 1 — Download & Run (Recommended)

1. Go to the [Releases](https://github.com/HackerJbon1337/J-Filer/releases) page
2. Download **`J-Filer.exe`**
3. Double-click to launch — that's it!

> No Python, no terminal, no setup required. The app opens in your browser automatically.

### Option 2 — Run from Source

```bash
# Clone the repo
git clone https://github.com/HackerJbon1337/J-Filer.git
cd J-Filer

# Install dependencies
pip install -r requirements.txt

# Launch the app
python app.py
```

### Option 3 — Build the Installer Yourself

```bash
pyinstaller jfiler.spec --clean --noconfirm
# Output: dist/J-Filer.exe
```

Or just run `build.bat` on Windows.

---

## 📁 Project Structure

```
J-Filer/
├── app.py               # Flask backend + desktop launcher
├── jfiler.spec          # PyInstaller build config
├── build.bat            # One-click build script
├── requirements.txt     # Python dependencies
├── setup.bat            # Dev setup script
├── mergers/
│   ├── pdf_merger.py    # PDF merge engine
│   ├── docx_merger.py   # DOCX merge engine
│   └── pptx_merger.py   # PPTX merge engine
├── converter/
│   └── converter.py     # Cross-format PDF converter
├── templates/
│   ├── landing.html     # Landing page
│   └── index.html       # Merger app UI
└── static/
    ├── index.css        # Liquid glass design system
    ├── app.js           # Frontend logic
    └── logo.png         # App logo
```

---

## 🔧 Merge Modes

### Same Format
| Input | Output |
|-------|--------|
| PDF + PDF | Single PDF |
| DOCX + DOCX | Single DOCX |
| PPTX + PPTX | Single PPTX |

### Cross-Format *(requires MS Office)*
| Input | Output |
|-------|--------|
| PDF + DOCX + PPTX | Unified PDF |
| DOCX + PPTX | Combined PDF |

---

## 🗜️ Compress Output

Enable the **Compress Output** toggle before merging to reduce the final file size:

- **PDF** — Rewrites the PDF with compressed content streams, object deduplication, and linearization using `pikepdf`.
- **DOCX / PPTX** — Re-compresses embedded images (downscales images > 1920px, converts to optimised JPEG at quality 72) using `Pillow`.

If compression fails for any reason, the original merged file is returned safely.

---

## 📦 Dependencies

```
flask
PyPDF2
python-docx
python-pptx
comtypes
pywin32
pikepdf      # PDF compression
Pillow       # Image compression for DOCX/PPTX
```

---

## 📄 License

MIT License — free to use, modify, and distribute.
