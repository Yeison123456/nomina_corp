@echo off
REM Inicia Libra — Sistema de Nómina en http://127.0.0.1:8000
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo No se encontro el entorno virtual. Siga los pasos de instalacion del README.md
    pause
    exit /b 1
)
start "" http://127.0.0.1:8000
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
