@echo off
cd /d "%~dp0"

echo ============================================
echo  [1/2] Construyendo TONI.exe (v3.5 + Whisper completo)...
echo ============================================
pyinstaller --noconsole --onedir --name TONI --clean --icon=toni.ico ^
  --add-data "toni.ico;." ^
  --add-data "whisper-cli.exe;." ^
  --add-data "ggml-small.bin;." ^
  --add-data "*.dll;." ^
  --add-data "vosk-model-small-es-0.42;vosk-model-small-es-0.42" ^
  --collect-data customtkinter --collect-all vosk --collect-all sounddevice ^
  --collect-submodules win32com --hidden-import win32com.client toni_gui.py
if errorlevel 1 (
    echo.
    echo ERROR en el build del exe. Revisa el mensaje de arriba.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  [2/2] Compilando instalador...
echo ============================================
if exist "C:\Program Files\Inno Setup 7\ISCC.exe" (
    "C:\Program Files\Inno Setup 7\ISCC.exe" toni_setup.iss
) else (
    echo Inno Setup no encontrado en la ruta default, salteando instalador.
)

echo.
echo LISTO. Exe en dist\TONI\ y setup en Output\.
pause