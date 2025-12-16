# Migration Guide: Desktop → Web Edition

## Overview

This guide helps you migrate from the old CustomTkinter desktop application to the new web-based system.

## Key Differences

### Architecture
| Aspect | Old System | New System |
|--------|-----------|------------|
| **Interface** | CustomTkinter (Desktop GUI) | Flask Web App |
| **Platform** | Windows only | Cross-platform (Pi optimized) |
| **Access** | Local machine only | Network-wide access |
| **Display Required** | Yes | No |
| **Multi-user** | No | Yes (with authentication) |

### Face Capture
| Aspect | Old System | New System |
|--------|-----------|------------|
| **Images per person** | 100 | 5 (smart angle detection) |
| **Capture method** | Continuous frames | Angle-based intelligent capture |
| **Processing time** | 10-30 seconds | 5-10 seconds |
| **Storage per person** | ~2-5 MB | ~500 KB |

### Data Storage
| Aspect | Old System | New System |
|--------|-----------|------------|
| **Face encodings** | MySQL BLOB | Pickle files on disk |
| **Read speed** | Slower (DB query) | Faster (file system) |
| **Backup** | Database dump | File copy |
| **Portability** | Tied to DB | Easily transferable |

### Performance
| Aspect | Old System | New System |
|--------|-----------|------------|
| **Frame processing** | Every frame | Every 3rd frame (configurable) |
| **Resolution** | Full resolution | Scaled down (configurable) |
| **CPU usage** | High | Optimized for Pi |
| **Memory usage** | High | Moderate |

## Migration Steps

### 1. Database Setup

The new system uses the **same database schema**, so no migration needed!

```sql
-- Your existing tables work as-is:
-- student_face, staff_face
-- student_attendance, staff_attendance
```

**Note**: The `Encoding` column in `student_face` and `staff_face` is no longer used. Face data is now stored in `face_data/` directory.

### 2. Face Data Migration

You need to regenerate face encodings from existing photos:

```python
# migration_script.py
from backend.core.face_recognition_engine import FaceRecognitionEngine
from backend.models.database import Database
import os

engine = FaceRecognitionEngine()
db = Database()

# Migrate students
students = db.fetch_data("SELECT ID, Name FROM student_face")
for student_id, name in students:
    image_folder = f"./Student_Face/{student_id}"
    if os.path.exists(image_folder):
        encodings = engine.generate_encodings_from_images(image_folder)
        if encodings:
            engine.save_encodings_to_file(student_id, encodings, name, 'student')
            print(f"Migrated {student_id} - {name}")

# Migrate staff
staff = db.fetch_data("SELECT ID, Name FROM staff_face")
for staff_id, name in staff:
    image_folder = f"./Staff_Face/{staff_id}"
    if os.path.exists(image_folder):
        encodings = engine.generate_encodings_from_images(image_folder)
        if encodings:
            engine.save_encodings_to_file(staff_id, encodings, name, 'staff')
            print(f"Migrated {staff_id} - {name}")
```

### 3. Configuration Mapping

Old `config.json` → New `config/config.json`:

```python
# OLD FORMAT
{
    "camera_choice": 0,
    "audio_choice": 1,  # REMOVED (no audio in web version)
    "auto_start": 0,    # REMOVED
    "camera_ip": "rtsp://...",
    "scale": 0.7,
    "max_checkin": "09:30:00",
    "min_checkout": "13:30:00",
    "db_connection": { ... }
}

# NEW FORMAT
{
    "camera_choice": 0,
    "camera_ip": "",
    "scale": 0.5,  # Lower for Pi
    "face_capture_count": 5,  # NEW
    "face_angle_threshold": 15.0,  # NEW
    "recognition_tolerance": 0.42,
    "recognition_threshold": 0.6,  # NEW (replaces threshold=70/100)
    "frame_skip": 2,  # NEW
    "max_checkin": "09:30:00",
    "min_checkout": "13:30:00",
    "db_connection": { ... },
    "secret_key": "...",  # NEW
    "jwt_expiration_hours": 24,  # NEW
    "admin_users": [...]  # NEW
}
```

### 4. Feature Mapping

#### Old → New Feature Equivalents

**Home Frame (Attendance)**
- Old: `home_frame.py` → Click "Take Attendance"
- New: Web UI → `/attendance` page → "Start Monitoring"

**Add Data Frame (Enrollment)**
- Old: `add_data_frame.py` → Fill form → Capture 100 images
- New: Web UI → `/enrollment` page → Fill form → Capture 5 smart images

**Data Frame (View Records)**
- Old: `data_frame.py` → Table view with filters
- New: Web UI → `/reports` page → Filters + Export

**Toggle Button**
- Old: `toggle_button.py` → Student/Staff switcher
- New: JavaScript toggle buttons in enrollment page

#### Removed Features
- ❌ Audio announcements (pyttsx3)
- ❌ Desktop window controls
- ❌ Local splash screen
- ❌ Auto-start option

#### New Features
- ✅ Web-based authentication
- ✅ Network streaming
- ✅ CSV export
- ✅ Dashboard with statistics
- ✅ Multi-user access
- ✅ RESTful API
- ✅ Smart angle-based capture

## Code Comparison

### Old: Desktop App Startup
```python
# main.py (OLD)
from customtkinter import *
app = FaceAttendanceSystem(CTk)
app.mainloop()
```

### New: Web App Startup
```python
# app.py (NEW)
from flask import Flask
app = create_app()
app.run(host='0.0.0.0', port=5000)
```

### Old: Face Capture Logic
```python
# add_data_frame.py (OLD)
while self.frame_count < 100:
    ret, frame = self.cap.read()
    if face_detected:
        self.frame_count += 1
        cv2.imwrite(f"{folder}/{frame_count}.jpg", face)
```

### New: Smart Face Capture
```python
# face_capture.py (NEW)
while len(captured_images) < 5:
    angles = calculate_face_angle(landmarks)
    if is_angle_different(angles):
        captured_images.append(face_img)
        captured_angles.append(angles)
```

### Old: Attendance Recognition
```python
# attendance.py (OLD)
known_face = get_known_face()  # From DB
for profile in known_face:
    if prediction(profile[2], face_encoding):
        mark_attendance(profile[0])
```

### New: Attendance Recognition
```python
# face_recognition_engine.py (NEW)
known_faces = load_all_face_data()  # From files
result = predict_face(face_encoding)
if result:
    attendance_queue.put(result)  # Async marking
```

## User Workflow Comparison

### Old Workflow (Desktop)

1. Run `main.exe` on Windows
2. Click "Take Attendance" → Window opens
3. Faces detected and marked
4. Click "Add Data" → Fill form
5. Click "Start" → Capture 100 images
6. View data in table

### New Workflow (Web)

1. Access `http://pi-address:5000` from any device
2. Login with credentials
3. Dashboard shows overview
4. Go to Attendance → Start Monitoring
5. Go to Enrollment → Fill form → Smart capture 5 images
6. Go to Reports → View/export data

## Performance Comparison

### Desktop System (Windows PC)
- ✅ Fast processing (powerful CPU)
- ✅ High resolution
- ❌ Requires display
- ❌ Local access only
- ❌ Not portable

### Web System (Raspberry Pi)
- ✅ Network accessible
- ✅ No display needed
- ✅ Portable & affordable
- ✅ Always-on capability
- ⚠️ Slower processing (optimized with frame skip)

## Troubleshooting Common Migration Issues

### Issue: "Face encodings not found"
**Solution**: Run the migration script to regenerate encodings from photos.

### Issue: "Old photos show blurry faces"
**Solution**: Re-enroll persons with new smart capture (better quality with 5 images).

### Issue: "Different recognition accuracy"
**Solution**: Adjust `recognition_threshold` in config. Old system used 70%, new default is 60%.

### Issue: "Missing database tables"
**Solution**: Database schema is the same. Just ensure MySQL is accessible.

### Issue: "Can't access from network"
**Solution**: Check firewall, ensure Pi is on network, use correct IP address.

## Recommendations

### For Best Results

1. **Re-enroll important persons**: The new 5-image smart capture provides better quality
2. **Adjust thresholds**: Start with default, tune based on accuracy
3. **Use Raspberry Pi 4**: With 4GB+ RAM for best performance
4. **Keep old system**: As backup during transition period
5. **Test thoroughly**: Before full deployment

### Migration Checklist

- [ ] Copy database credentials to new config
- [ ] Transfer image folders (Student_Face, Staff_Face)
- [ ] Run face encoding migration script
- [ ] Test recognition with existing persons
- [ ] Re-enroll critical persons with smart capture
- [ ] Configure admin users
- [ ] Test from multiple devices
- [ ] Set up as system service
- [ ] Configure backup
- [ ] Update staff training/documentation

## Support

If you encounter issues during migration:
1. Check both README.md files
2. Verify database connectivity
3. Test face recognition accuracy
4. Compare old vs new config settings
5. Consider re-enrollment for better results
