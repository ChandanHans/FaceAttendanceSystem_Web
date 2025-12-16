# Face Attendance System - Web Edition

A modern web-based face recognition attendance system optimized for Raspberry Pi, built with Flask and designed to work without a display.

## Features

- 🎯 **Smart Face Capture**: Captures only 5 images with different angles (not 100!)
- 🌐 **Web-Based Interface**: Access from any device on the network
- 🔐 **Authentication System**: Secure JWT-based login
- 📊 **Real-time Attendance**: Live video streaming with face recognition
- 📈 **Reports & Analytics**: Generate attendance reports with export to CSV
- 🚀 **Raspberry Pi Optimized**: Frame skipping and efficient processing
- 💾 **File-Based Storage**: Face encodings stored as files for better performance

## Architecture

```
FaceAttendanceSystem_Web/
├── backend/
│   ├── api/              # REST API endpoints
│   │   ├── auth.py       # Authentication
│   │   ├── attendance.py # Attendance monitoring
│   │   ├── enrollment.py # Face enrollment
│   │   └── reports.py    # Reports generation
│   ├── core/             # Core logic
│   │   ├── face_capture.py           # Smart face capture
│   │   └── face_recognition_engine.py # Recognition logic
│   ├── models/           # Database models
│   │   └── database.py
│   ├── static/           # Web assets (CSS, JS)
│   └── templates/        # HTML templates
├── face_data/            # Face encodings storage
├── config/               # Configuration files
└── app.py                # Main Flask application
```

## Installation

### For Development (Windows/Mac/Linux)

1. Create virtual environment:
```bash
cd FaceAttendanceSystem_Web
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure database:
- Update `config/config.json` with your MySQL credentials
- Use the same database from the old system

4. Run the application:
```bash
python app.py
```

5. Access at: `http://localhost:5000`
   - Default login: `admin` / `admin123`

### For Raspberry Pi

1. Update system:
```bash
sudo apt-get update
sudo apt-get upgrade
```

2. Install dependencies:
```bash
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y cmake libopenblas-dev liblapack-dev
sudo apt-get install -y libjpeg-dev zlib1g-dev
```

3. Install dlib (takes time on Pi):
```bash
pip3 install dlib
```

4. Install other requirements:
```bash
cd FaceAttendanceSystem_Web
pip3 install -r requirements_pi.txt
```

5. Configure and run:
```bash
python3 app.py
```

6. Access from network: `http://<raspberry-pi-ip>:5000`

## Configuration

Edit `config/config.json`:

```json
{
    "camera_choice": 0,              // Camera index
    "face_capture_count": 5,         // Number of images to capture
    "face_angle_threshold": 15.0,    // Angle difference threshold
    "recognition_tolerance": 0.42,    // Face matching tolerance
    "recognition_threshold": 0.6,     // Match percentage required
    "frame_skip": 2,                  // Process every Nth frame
    "max_checkin": "09:30:00",       // Staff check-in deadline
    "min_checkout": "13:30:00",      // Staff check-out start time
    "secret_key": "change-this-in-production",
    "db_connection": {
        "host": "localhost",
        "user": "root",
        "passwd": "your-password",
        "db": "face_recognizer"
    }
}
```

## Usage

### 1. Login
- Navigate to `/login`
- Use default credentials or configured admin users

### 2. Enroll New Person
- Go to **Enrollment** page
- Select Student or Staff
- Fill in details
- Click "Start Capture"
- Turn head slowly to capture 5 different angles
- System automatically detects angle changes
- Click "Complete Enrollment"

### 3. Start Attendance Monitoring
- Go to **Attendance** page
- Select camera source
- Click "Start Monitoring"
- View live feed with face recognition
- Attendance is automatically marked in database

### 4. View Reports
- Go to **Reports** page
- Select filters (role, date range, person)
- Click "Load Report"
- Export to CSV if needed

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `GET /api/auth/verify` - Verify token
- `POST /api/auth/logout` - Logout

### Enrollment
- `POST /api/enrollment/start` - Start enrollment session
- `POST /api/enrollment/capture` - Capture frame
- `POST /api/enrollment/complete` - Complete enrollment
- `GET /api/enrollment/list` - List enrolled persons
- `DELETE /api/enrollment/delete/<id>` - Delete person

### Attendance
- `POST /api/attendance/start` - Start monitoring
- `POST /api/attendance/stop` - Stop monitoring
- `GET /api/attendance/stream` - Video stream
- `GET /api/attendance/status` - System status

### Reports
- `GET /api/reports/attendance` - Get attendance records
- `GET /api/reports/summary` - Get summary

## Performance Optimization for Raspberry Pi

1. **Frame Skipping**: Process every 3rd frame (configurable)
2. **Resolution Scaling**: Scale down frames before processing
3. **Smart Capture**: Only 5 images instead of 100
4. **File Storage**: Encodings stored as files, not DB BLOBs
5. **Caching**: Known faces cached in memory

## Differences from Old System

| Feature | Old (Desktop) | New (Web) |
|---------|--------------|-----------|
| Interface | CustomTkinter GUI | Web Browser |
| Display | Required | Not Required |
| Access | Local only | Network-wide |
| Images Captured | 100 | 5 (smart angles) |
| Encoding Storage | MySQL BLOB | File system |
| Platform | Windows | Any (Pi optimized) |
| Multi-user | No | Yes (JWT auth) |

## Troubleshooting

### Camera not working
- Check camera permissions
- Try different camera index in config
- Ensure camera not used by other apps

### Slow performance on Pi
- Increase `frame_skip` in config
- Reduce `scale` value
- Use Pi 4 with 4GB+ RAM

### Database connection error
- Verify MySQL is running
- Check credentials in config
- Ensure database exists

## Security Notes

⚠️ **Important for Production**:
1. Change `secret_key` in config
2. Change default admin password
3. Use HTTPS (configure reverse proxy)
4. Keep face_data directory secure
5. Regular database backups

## License

Same as original project

## Credits

Refactored and modernized from the original Face Attendance System.
