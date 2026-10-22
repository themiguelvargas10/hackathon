@echo off
setlocal
cd /d "%~dp0"
title AquaGuard - Demo local
where py >nul 2>nul
if errorlevel 1 goto fallback
py -3.12 -c "import sys" >nul 2>nul
if errorlevel 1 goto fallback
py -3.12 server.py
goto done
:fallback
where python >nul 2>nul
if errorlevel 1 goto missing
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 goto missing
python server.py
goto done
:missing
echo Instala Python 3.12 y vuelve a abrir este archivo.
echo No se necesitan paquetes adicionales ni claves de API.
:done
pause
