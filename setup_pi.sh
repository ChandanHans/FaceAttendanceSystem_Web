#!/bin/bash
# Setup script for Face Attendance System Web Edition on Raspberry Pi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================="
echo "Face Attendance System - Pi Setup"
echo "========================================="
echo ""
echo "Working directory: $SCRIPT_DIR"
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

echo ""
echo "========================================="
echo "🗄️  Checking MySQL Configuration"
echo "========================================="
echo ""

# Check if config exists
if [ ! -f config/config.json ]; then
    echo "⚠️  config/config.json not found!"
else
    # Check if host is localhost
    DB_HOST=$(python3 -c "import json; config = json.load(open('config/config.json')); print(config['db_connection']['host'])" 2>/dev/null)
    
    if [ "$DB_HOST" == "localhost" ]; then
        echo "Detected localhost MySQL configuration"
        echo "Checking MySQL connection..."
        
        # Try to connect to MySQL
        python3 -c "import mysql.connector; mysql.connector.connect(host='localhost', user='root', passwd='8258')" 2>/dev/null
        
        if [ $? -ne 0 ]; then
            echo ""
            echo "❌ MySQL connection failed!"
            echo ""
            echo "MySQL/MariaDB Server is not installed or not running."
            echo ""
            echo "Installing MariaDB Server (MySQL replacement for Pi)..."
            sudo apt-get install -y mariadb-server mariadb-client
            
            echo ""
            echo "Starting MariaDB service..."
            sudo systemctl start mariadb
            sudo systemctl enable mariadb
            
            echo ""
            echo "Setting up MariaDB root password..."
            echo "Suggested credentials:"
            echo "  Host: localhost"
            echo "  User: root"
            echo "  Password: FaceAttend2025!"
            echo "  Database: face_recognizer_web"
            echo ""
            
            read -p "Use these credentials? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                # Set MariaDB root password
                sudo mariadb -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'FaceAttend2025!';"
                sudo mariadb -e "FLUSH PRIVILEGES;"
                
                # Create database
                sudo mariadb -u root -pFaceAttend2025! -e "CREATE DATABASE IF NOT EXISTS face_recognizer_web;"
                
                # Update config.json
                python3 -c "
import json
with open('config/config.json', 'r') as f:
    config = json.load(f)
config['db_connection']['passwd'] = 'FaceAttend2025!'
with open('config/config.json', 'w') as f:
    json.dump(config, f, indent=4)
print('✅ Config updated!')
"
                echo "✅ MariaDB password set and config updated!"
                echo "✅ Database created!"
            else
                echo ""
                echo "Please update config/config.json manually with your MySQL/MariaDB credentials"
                read -p "Press Enter to edit config now..."
                nano config/config.json
            fi
        else
            echo "✅ MySQL connection successful!"
            echo ""
            echo "Creating database if not exists..."
            python3 -c "import mysql.connector; conn = mysql.connector.connect(host='localhost', user='root', passwd='8258'); cursor = conn.cursor(); cursor.execute('CREATE DATABASE IF NOT EXISTS face_recognizer_web'); print('✅ Database ready!')" 2>/dev/null
        fi
    else
        echo "Using remote MySQL server: $DB_HOST"
        echo "Skipping local MySQL setup"
    fi
fi

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. If MySQL setup failed, update config/config.json manually"
echo "2. Import database: mysql -u root -p face_recognizer_web < face_recognizer_web.sql"
echo "3. Run the application: ./run.sh"
echo "4. Access from browser: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Default login: admin / admin123"
echo ""
