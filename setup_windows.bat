@echo off
REM Setup script for Face Attendance System Web Edition on Windows

echo =========================================
echo Face Attendance System - Windows Setup
echo =========================================
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
