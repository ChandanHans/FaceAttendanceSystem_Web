# Face Attendance System - Web Edition

**Version:** 2.0  
**Platform:** Web-based (Raspberry Pi Optimized)  
**Python:** 3.8+

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure database in `config/config.json`

3. Run application:
   ```bash
   python app.py
   ```

4. Access at http://localhost:5000

5. Login with default credentials:
   - Username: `admin`
   - Password: `admin123`

## Key Features

✅ Web-based interface (no display needed)  
✅ Smart face capture (5 images with angle detection)  
✅ JWT authentication  
✅ Real-time attendance monitoring  
✅ Network-accessible  
✅ Raspberry Pi optimized  
✅ CSV export  

## Database Setup

Use the same MySQL database from the original system:
- `student_face` table
- `staff_face` table
- `student_attendance` table
- `staff_attendance` table

Face encodings are now stored as files in `face_data/` directory.

## Raspberry Pi Deployment

See README.md for detailed Pi installation instructions.

For Pi, use:
```bash
pip install -r requirements_pi.txt
```

## Configuration

Edit `config/config.json` to customize:
- Camera settings
- Face capture parameters
- Recognition thresholds
- Check-in/out times
- Database credentials
- Admin users

## Network Access

From any device on the network:
```
http://<raspberry-pi-ip>:5000
```

Example: http://192.168.1.100:5000

## Support

For issues or questions, refer to the full README.md file.
