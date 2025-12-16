# Deployment Guide for Raspberry Pi

## Hardware Requirements

- Raspberry Pi 4 (4GB RAM recommended)
- MicroSD card (16GB minimum, 32GB recommended)
- USB Webcam or Pi Camera Module
- Network connection (WiFi or Ethernet)
- Power supply

## Software Requirements

- Raspbian OS (Bullseye or later)
- MySQL/MariaDB server
- Python 3.8+

## Installation Steps

### 1. Prepare Raspberry Pi

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install MySQL
sudo apt-get install mariadb-server -y
sudo mysql_secure_installation
```

### 2. Setup Database

```bash
# Login to MySQL
sudo mysql -u root -p

# Create database and user
CREATE DATABASE face_recognizer;
CREATE USER 'attendance_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON face_recognizer.* TO 'attendance_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Import schema from old system
mysql -u attendance_user -p face_recognizer < /path/to/face_recognation.sql
```

### 3. Transfer Application

```bash
# Copy to Pi (from your computer)
scp -r FaceAttendanceSystem_Web pi@<pi-ip-address>:~/

# Or clone from git if you pushed it
ssh pi@<pi-ip-address>
cd ~
git clone <your-repo-url> FaceAttendanceSystem_Web
```

### 4. Run Setup Script

```bash
cd ~/FaceAttendanceSystem_Web
chmod +x setup_pi.sh
./setup_pi.sh
```

This will take 30-60 minutes as it compiles dlib.

### 5. Configure Application

```bash
nano config/config.json
```

Update:
- Database credentials
- Camera settings
- Admin password (IMPORTANT!)

### 6. Test Run

```bash
source venv/bin/activate
python3 app.py
```

Access from browser: `http://<pi-ip>:5000`

### 7. Install as System Service

```bash
# Copy service file
sudo cp face-attendance.service /etc/systemd/system/

# Edit paths if needed
sudo nano /etc/systemd/system/face-attendance.service

# Enable and start service
sudo systemctl enable face-attendance
sudo systemctl start face-attendance

# Check status
sudo systemctl status face-attendance

# View logs
sudo journalctl -u face-attendance -f
```

## Network Configuration

### Port Forwarding (Optional)

If you want to access from outside your local network:

```bash
# Edit app.py to run on different port if needed
# Then configure your router to forward port 5000 to Pi's IP
```

### Static IP (Recommended)

```bash
# Edit dhcpcd.conf
sudo nano /etc/dhcpcd.conf

# Add at end:
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

## Security Recommendations

1. **Change Default Password**
   - Edit config/config.json
   - Change admin password

2. **Use HTTPS**
   ```bash
   # Install nginx as reverse proxy
   sudo apt-get install nginx
   
   # Configure SSL with Let's Encrypt
   sudo apt-get install certbot python3-certbot-nginx
   ```

3. **Firewall**
   ```bash
   sudo apt-get install ufw
   sudo ufw allow 22
   sudo ufw allow 5000
   sudo ufw enable
   ```

4. **Regular Updates**
   ```bash
   # Create cron job
   sudo crontab -e
   
   # Add:
   0 2 * * 0 apt-get update && apt-get upgrade -y
   ```

## Performance Tuning

### Increase Swap (if <4GB RAM)

```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Optimize Config

In `config/config.json`:
```json
{
    "scale": 0.4,           // Lower = faster but less accurate
    "frame_skip": 3,        // Higher = faster but may miss faces
    "face_capture_count": 5 // Keep at 5 for best balance
}
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u face-attendance -n 50

# Check if port in use
sudo lsof -i :5000

# Test manually
cd ~/FaceAttendanceSystem_Web
source venv/bin/activate
python3 app.py
```

### Camera not detected
```bash
# List video devices
v4l2-ctl --list-devices

# Test camera
raspistill -o test.jpg  # For Pi Camera
ffplay /dev/video0      # For USB camera
```

### Slow performance
- Reduce resolution in camera settings
- Increase frame_skip in config
- Use Pi 4 with 4GB+ RAM
- Enable hardware acceleration

### Database connection errors
```bash
# Check MySQL is running
sudo systemctl status mariadb

# Test connection
mysql -u attendance_user -p face_recognizer
```

## Backup

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/pi/backups"

mkdir -p $BACKUP_DIR

# Backup database
mysqldump -u attendance_user -p'your_password' face_recognizer > $BACKUP_DIR/db_$DATE.sql

# Backup face data
tar -czf $BACKUP_DIR/face_data_$DATE.tar.gz face_data/ Student_Face/ Staff_Face/

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Schedule with cron:
```bash
crontab -e
# Add: 0 3 * * * /home/pi/backup.sh
```

## Maintenance

### Check System Status
```bash
# Service status
sudo systemctl status face-attendance

# Disk space
df -h

# Memory usage
free -h

# CPU temperature
vcgencmd measure_temp
```

### Update Application
```bash
cd ~/FaceAttendanceSystem_Web
source venv/bin/activate
git pull  # If using git
pip install -r requirements_pi.txt --upgrade
sudo systemctl restart face-attendance
```

## Remote Access

### VNC Setup
```bash
sudo apt-get install realvnc-vnc-server
sudo raspi-config
# Interface Options -> VNC -> Enable
```

### SSH Tunnel
```bash
# From your computer
ssh -L 5000:localhost:5000 pi@<pi-ip>
# Then access http://localhost:5000
```

## Support

For issues:
1. Check logs: `sudo journalctl -u face-attendance -n 100`
2. Test components individually
3. Verify configuration
4. Check network connectivity
5. Refer to main README.md
