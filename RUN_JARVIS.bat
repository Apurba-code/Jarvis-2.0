@echo off
echo Starting JARVIS AR Interface System...
echo.

cd /d "%~dp0"

REM Try python via various commands
python launch.py
if %ERRORLEVEL% EQU 0 goto :success

py launch.py
if %ERRORLEVEL% EQU 0 goto :success

python3 launch.py
if %ERRORLEVEL% EQU 0 goto :success

echo.
echo ERROR: Launch failed. Please ensure Python is installed.
pause
goto :eof

:success
echo JARVIS System Shutdown.
