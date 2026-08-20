@echo off
setlocal
where py >nul 2>nul
if errorlevel 1 (
  echo.
  echo This file is for developers/build machines only.
  echo Python was not found.
  echo.
  echo If you only want to use the app, use the GitHub Actions installer artifact:
  echo FreePDFEditorPro-Setup.exe
  pause
  exit /b 1
)
py -3.11 -m pip install -r requirements.txt || exit /b 1
py -3.11 -m pip install pyinstaller || exit /b 1
py -3.11 -m PyInstaller --noconfirm --clean --windowed --name FreePDFEditorPro app\main.py || exit /b 1
echo.
echo Build complete: dist\FreePDFEditorPro\FreePDFEditorPro.exe
pause
