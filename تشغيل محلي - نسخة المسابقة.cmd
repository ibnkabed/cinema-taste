@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=C:\Users\abdul\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "PYTHONW=C:\Users\abdul\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"

if not exist "%PYTHON%" (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python runtime was not found.
    pause
    exit /b 1
  )
  set "PYTHON=python"
)

if not exist "%PYTHONW%" set "PYTHONW=%PYTHON%"

start "" "%PYTHONW%" "%~dp0tools\cinema_server.py" --no-open --port 18765
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:18765/"

endlocal
