# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Universal Document Merger (J-Filer).
Bundles the Flask app + templates + static files into a single .exe.
"""

import os

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('mergers', 'mergers'),
        ('converter', 'converter'),
    ],
    hiddenimports=[
        'flask',
        'jinja2',
        'PyPDF2',
        'docx',
        'pptx',
        'comtypes',
        'win32com',
        'win32com.client',
        'pikepdf',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='J-Filer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # No console window — runs silently
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('static', 'logo.png'),
)
