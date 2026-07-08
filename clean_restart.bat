@echo off
REM ============================================================================
REM Clean Restart Script - Forces Python to reload all modules
REM ============================================================================

echo.
echo ========================================================================
echo   CLEAN RESTART
echo ========================================================================
echo.
echo Stopping all Python processes and clearing cache...
echo.

REM Step 1: Kill all Python processes (ensures no old instances running)
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul

REM Step 2: Delete all __pycache__ directories recursively
echo Clearing __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Step 3: Delete all .pyc files
echo Clearing .pyc files...
del /s /q *.pyc >nul 2>&1

REM Step 4: Wait a moment for filesystem to settle
timeout /t 1 /nobreak >nul

echo.
echo Cache cleared successfully!
echo Starting application with fresh modules...
echo.

REM Step 5: Start with -B flag (don't write bytecode)
py -B main.py

REM If main.py fails, try run.bat
if errorlevel 1 (
    echo.
    echo Trying run.bat instead...
    call run.bat
)

echo.
pause
