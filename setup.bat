@echo off
echo ===================================
echo  Universal Document Merger - Setup
echo ===================================
echo.

echo [1/2] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    echo Make sure Python and pip are installed.
    pause
    exit /b 1
)

echo.
echo [2/2] Launching application...
python app.py

pause
