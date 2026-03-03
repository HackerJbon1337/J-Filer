# J-Filer — Universal Document Merger

A high-performance, offline desktop application for merging and consolidating **PPTX**, **DOCX**, and **PDF** files into a single structured output.

Built with Python, Flask, and a stunning **Liquid Glass** UI — runs entirely offline.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **PDF Merge** | Combine multiple PDFs into one |
| **DOCX Merge** | Merge Word documents with page breaks |
| **PPTX Merge** | Concatenate PowerPoint slides |
| **Cross-Format** | Mix PPTX + DOCX + PDF → unified PDF |
| **Drag & Drop** | Beautiful file upload with drag-and-drop |
| **Progress Bar** | Real-time percentage during merge |
| **Offline** | 100% local — no internet required |
| **Liquid Glass UI** | Premium dark theme with iridescent effects |

---

## 🚀 Installation

### Option 1 — Download & Run (Recommended)

1. Go to the [Releases](https://github.com/YOUR_USERNAME/J-Filer/releases) page
2. Download **`J-Filer.exe`**
3. Double-click to launch — that's it!

> No Python, no terminal, no setup required. The app opens in your browser automatically.

### Option 2 — Run from Source

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/J-Filer.git
cd J-Filer

# Install dependencies
pip install -r requirements.txt

# Launch the app
python app.py
```

### Option 3 — Build the Installer Yourself

```bash
# Install PyInstaller
pip install pyinstaller

# Build the .exe
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

## 📄 License

MIT License — free to use, modify, and distribute.
