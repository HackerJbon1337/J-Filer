@echo off
echo ============================================
echo  J-Filer — Building Standalone Installer
echo ============================================
echo.

echo [1/3] Installing PyInstaller...
pip install pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller.
    pause
    exit /b 1
)

echo [2/3] Building J-Filer.exe...
pyinstaller jfiler.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo.
echo  Your installer is at:
echo    dist\J-Filer.exe
echo.
echo  Users can just double-click J-Filer.exe to run the app.
echo  No Python or terminal required!
echo.
pause
