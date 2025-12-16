#!/bin/bash
# Run script for Face Attendance System

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================="
echo "Face Attendance System - Starting"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run setup_pi.sh first to create the environment."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found!"
    exit 1
fi

# Run the application
echo "🚀 Starting Face Attendance System..."
echo "📍 Access at: http://$(hostname -I | awk '{print $1}'):5000"
echo "🔑 Default login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
