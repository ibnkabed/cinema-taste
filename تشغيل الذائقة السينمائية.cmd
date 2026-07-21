@echo off
setlocal
cd /d "%~dp0"

where pyw >nul 2>nul
if not errorlevel 1 (
  start "" pyw -3 "tools\cinema_server.py" --no-open --port 18765
  goto open_app
)

where pythonw >nul 2>nul
if not errorlevel 1 (
  start "" pythonw "tools\cinema_server.py" --no-open --port 18765
  goto open_app
)

where py >nul 2>nul
if not errorlevel 1 (
  start "" py -3 "tools\cinema_server.py" --no-open --port 18765
  goto open_app
)

where python >nul 2>nul
if not errorlevel 1 (
  start "" python "tools\cinema_server.py" --no-open --port 18765
  goto open_app
)

echo Python 3.10 or newer was not found. Install Python, then run this launcher again.
pause
exit /b 1

:open_app
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:18765/?lang=en"

endlocal
