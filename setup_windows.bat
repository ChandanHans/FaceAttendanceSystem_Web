@echo off
REM Setup script for Face Attendance System Web Edition on Windows

echo =========================================
echo Face Attendance System - Windows Setup
echo =========================================
echo.

echo Checking Python version...
set PYTHON_CMD=python
set REQUIRED_VERSION=3.11.9

REM Check if Python 3.11.9 is available
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Python 3.11.x via py launcher
    set PYTHON_CMD=py -3.11
    goto :create_venv
)

REM Check if python3.11 command exists
python3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found python3.11 command
    set PYTHON_CMD=python3.11
    goto :create_venv
)

REM Check default python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set CURRENT_VERSION=%%i
echo Current Python version: %CURRENT_VERSION%
if "%CURRENT_VERSION%" == "%REQUIRED_VERSION%" (
    echo Python 3.11.9 is already the default version
    goto :create_venv
)

echo.
echo Python 3.11.9 not found!
echo Please install Python 3.11.9 from:
echo https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
echo.
echo Installation tips:
echo - Check "Add Python to PATH" during installation
echo - Or install for all users to use py launcher
echo.
set /p CONTINUE="Continue with current Python version (%CURRENT_VERSION%)? (y/n): "
if /i not "%CONTINUE%" == "y" (
    echo Setup cancelled.
    pause
    exit /b 1
)

:create_venv
echo Creating virtual environment with %PYTHON_CMD%...
%PYTHON_CMD% -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python packages...
pip install --upgrade pip
pip install -r requirements.txt

echo Creating necessary directories...
if not exist "face_data" mkdir face_data
if not exist "Student_Face" mkdir Student_Face
if not exist "Staff_Face" mkdir Staff_Face

echo.
echo =========================================
echo Setup Complete!
echo =========================================
echo.
echo Next steps:
echo 1. Edit config/config.json with your database credentials
echo 2. Ensure MySQL database is set up
echo 3. Run: python app.py
echo 4. Access at: http://localhost:5000
echo.
echo Default login: admin / admin123
echo.
pause
