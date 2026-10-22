@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3.12 -m venv .venv
  if errorlevel 1 (echo Instala Python 3.12 desde python.org y vuelve a abrir este archivo.& pause & exit /b 1)
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)
.venv\Scripts\python.exe server.py
pause
