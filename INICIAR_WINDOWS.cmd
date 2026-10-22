@echo off
cd /d "%~dp0"
if not exist data\operaciones_simuladas.csv (
  echo Copia el CSV autorizado en data\operaciones_simuladas.csv
  pause
  exit /b 1
)
docker compose up --build -d
if errorlevel 1 (
  echo Revisa que Docker Desktop este iniciado. Consulta README.md.
  pause
  exit /b 1
)
echo Abre http://127.0.0.1:8501 cuando el contenedor este healthy.
docker compose ps
pause
