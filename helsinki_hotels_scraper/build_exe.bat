@echo off
echo ============================================
echo   Building Helsinki Hotels Scraper EXE
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Installing required packages...
pip install -r requirements.txt

echo.
echo Building executable with PyInstaller...
echo.

REM Build the GUI version as a single executable
pyinstaller --onefile ^
    --windowed ^
    --name "Helsinki_Hotels_Scraper" ^
    --add-data "requirements.txt;." ^
    --hidden-import=openpyxl ^
    --hidden-import=pandas ^
    --hidden-import=requests ^
    --hidden-import=bs4 ^
    --hidden-import=tkinter ^
    hotel_scraper_gui.py

echo.
echo ============================================
if exist "dist\Helsinki_Hotels_Scraper.exe" (
    echo BUILD SUCCESSFUL!
    echo.
    echo Your executable is located at:
    echo   dist\Helsinki_Hotels_Scraper.exe
    echo.
    echo You can distribute this single .exe file to customers.
) else (
    echo BUILD FAILED!
    echo Please check the error messages above.
)
echo ============================================
echo.
pause
