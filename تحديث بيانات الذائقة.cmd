@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
  py -3 "tools\cinema_server.py" --refresh-only
  goto refresh_done
)

where python >nul 2>nul
if not errorlevel 1 (
  python "tools\cinema_server.py" --refresh-only
  goto refresh_done
)

echo Python 3.10 or newer was not found.
pause
exit /b 1

:refresh_done
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
