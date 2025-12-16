@echo off
REM Setup script for Face Attendance System Web Edition on Windows

echo =========================================
echo Face Attendance System - Windows Setup
echo =========================================
echo.

echo Checking Python version...
python --version 2>&1 | findstr /C:"3.11.9" >nul
if errorlevel 1 (
    echo WARNING: Python 3.11.9 is recommended
    python --version
    echo.
    echo To install Python 3.11.9:
    echo 1. Download from: https://www.python.org/downloads/release/python-3119/
    echo 2. Install and add to PATH
    echo 3. Run this setup script again
    echo.
    choice /C YN /M "Continue with current version"
    if errorlevel 2 exit /b 1
) else (
    echo Found Python 3.11.9 - OK
)
echo.

echo Creating virtual environment...
python -m venv venv

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
