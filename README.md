# J-Filer — The Ultimate Document Toolkit

A high-performance, offline desktop application suite for **Merging**, **Converting**, **Inverting**, and **Compressing** your PPTX, DOCX, PDF, and Image files.

Built with Python, Flask, and a stunning **React-Bits inspired Liquid Glass UI** — runs entirely offline.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square)
[![Download Latest Release](https://img.shields.io/badge/Download-Latest_Release-ff69b4?style=flat-square&logo=github)](https://github.com/HackerJbon1337/J-Filer/releases/latest)

---

## ✨ The 5-in-1 Toolkit

| Tool | Description |
|---------|-------------|
| **Merger** | Combine unlimited PDFs, DOCXs, or PPTXs into single files |
| **Converter** | Convert PDFs, DOCXs, and PPTXs to PDF. Instantly turn JPG/PNG/WEBP images into PDFs or PPTX files |
| **Compressor** | Aggressively shrink PDF, DOCX, and PPTX files by safely downscaling embedded images offline |
| **Inverter** | Invert the colours of PDF and PPTX files for dark-mode reading and printing |
| **Cross-Format** | Mix PPTX + DOCX + PDF and merge them completely into a unified PDF |

### Core Features
- **Drag & Drop** Beautiful file upload zones with drag-and-drop
- **Progress Bar** Real-time task progress tracking
- **100% Offline** Your files never leave your computer
- **Liquid Glass UI** Premium dark theme with interactive 3D Vanilla Tilt animations

---

## 🚀 Installation

### Option 1 — Download & Run (Recommended)

1. Go to the [Releases](https://github.com/HackerJbon1337/J-Filer/releases) page
2. Download **`J-Filer-Setup.exe`**
3. Install the application. A shortcut will automatically be created on your Desktop!

> No Python, no terminal, no setup required. The standalone app opens via an optimized offline server.

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
# First, generate the standalone core:
.\build.bat

# Then, build the setup wizard using Inno Setup Compiler
iscc setup.iss
# Output: Output/J-Filer-Setup.exe
```

---

## 🗜️ Aggressive Compression Engine

The standalone Compressor tool shrinks file sizes remarkably without ruining visual quality:

- **PDF Compression**: Uses `PyMuPDF (fitz)` and `Pillow` to actively extract, downscale (max height/width of 1200px), and heavily compress (JPEG Quality 50) all embedded images. Uses byte-comparison to ensure strict size reduction.
- **DOCX / PPTX Compression**: Similar heavy downscaling (1200px) and image re-compression using `Pillow` across all media objects.

---

## 📦 Core Dependencies

```
flask
PyPDF2
python-docx
python-pptx
PyMuPDF (fitz) # Deep PDF extraction
Pillow       # Image manipulation and compression
pikepdf      # Lossless PDF stream compression
pywin32      # Core Windows integrations
comtypes
```

---

## 📄 License

MIT License — free to use, modify, and distribute.
