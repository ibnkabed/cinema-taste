@echo off
setlocal
set "PYTHON=C:\Users\abdul\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if not exist "%PYTHON%" (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python runtime was not found.
    pause
    exit /b 1
  )
  set "PYTHON=python"
)

"%PYTHON%" "%~dp0tools\cinema_server.py" --refresh-only
if errorlevel 1 (
  echo.
  echo Data refresh failed.
  pause
  exit /b 1
)

echo.
echo Data refresh completed successfully.
pause
endlocal
