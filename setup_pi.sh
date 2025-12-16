#!/bin/bash
# Setup script for Face Attendance System Web Edition on Raspberry Pi

echo "========================================="
echo "Face Attendance System - Pi Setup"
echo "========================================="
echo ""

# Check if running on Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

echo "📦 Installing system dependencies..."
sudo apt-get install -y python3-pip python3-dev python3-venv
sudo apt-get install -y cmake libopenblas-dev liblapack-dev
sudo apt-get install -y libjpeg-dev zlib1g-dev
sudo apt-get install -y libatlas-base-dev
sudo apt-get install -y libhdf5-dev libhdf5-serial-dev
sudo apt-get install -y python3-opencv
sudo apt-get install -y build-essential libssl-dev libffi-dev
sudo apt-get install -y libsqlite3-dev libbz2-dev libreadline-dev

echo "🐍 Checking Python version..."
REQUIRED_VERSION="3.11.9"
PYTHON_CMD="python3"

# Check if Python 3.11.9 is available
if command -v python3.11 &> /dev/null; then
    CURRENT_VERSION=$(python3.11 --version | awk '{print $2}')
    echo "Found Python $CURRENT_VERSION"
    if [[ "$CURRENT_VERSION" == "3.11."* ]]; then
        PYTHON_CMD="python3.11"
        echo "✅ Using Python 3.11.x"
    fi
fi

# If Python 3.11 not found, try to install it
if [[ "$PYTHON_CMD" == "python3" ]]; then
    echo "⚠️  Python 3.11.9 not found. Attempting to install..."
    
    # Add deadsnakes PPA for Ubuntu/Debian (if applicable)
    if command -v add-apt-repository &> /dev/null; then
        echo "Adding deadsnakes PPA..."
        sudo apt-get install -y software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt-get update
        sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
        PYTHON_CMD="python3.11"
    else
        # For Raspberry Pi OS or systems without PPA support
        echo "Building Python 3.11.9 from source (this will take 30-60 minutes)..."
        cd /tmp
        wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
        tar -xf Python-3.11.9.tgz
        cd Python-3.11.9
        ./configure --enable-optimizations --with-ensurepip=install
        make -j $(nproc)
        sudo make altinstall
        cd ~
        PYTHON_CMD="python3.11"
    fi
    
    if command -v python3.11 &> /dev/null; then
        echo "✅ Python 3.11 installed successfully"
    else
        echo "❌ Failed to install Python 3.11. Using system default."
        PYTHON_CMD="python3"
    fi
fi

echo "🔧 Creating virtual environment with $PYTHON_CMD..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install wheel setuptools

echo "📦 Installing numpy (this may take a while)..."
pip install numpy==1.24.3

echo "📦 Installing dlib (this will take 30-60 minutes on Pi)..."
pip install dlib

echo "📦 Installing remaining packages..."
pip install -r requirements_pi.txt

echo "📁 Creating necessary directories..."
mkdir -p face_data
mkdir -p Student_Face
mkdir -p Staff_Face

echo "⚙️  Setting up configuration..."
if [ ! -f config/config.json ]; then
    echo "Please edit config/config.json with your database credentials"
else
    echo "Configuration file already exists"
fi

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit config/config.json with your database credentials"
echo "2. Ensure MySQL database is set up"
echo "3. Activate virtual environment: source venv/bin/activate"
echo "4. Run the application: python3 app.py"
echo "5. Access from browser: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Default login: admin / admin123"
echo ""
