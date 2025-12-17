# Using Laptop Camera Instead of ESP32-CAM

Since the ESP32-CAM is not working, you can use your laptop's camera as the video source for your Pi-based attendance system. Both devices need to be on the same network.

## 🎯 Overview

**Setup:**
- **Laptop (Windows)**: Runs the camera streaming server
- **Raspberry Pi**: Runs the main attendance system
- **Network**: Both connected to the same WiFi

**Current Configuration:**
- Laptop IP: `172.30.9.196`
- Camera Stream: `http://172.30.9.196:5001/video`

---

## 📋 Step-by-Step Setup

### Step 1: On Your Windows Laptop

1. **Open a terminal** in the project folder
   ```powershell
   cd "C:\Users\Chandan\Documents\My Projects\FaceAttendanceSystem_Web"
   ```

2. **Activate the virtual environment** (if not already active)
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. **Make sure Flask is installed**
   ```powershell
   pip install flask opencv-python
   ```

4. **Start the camera server**
   ```powershell
   python laptop_camera_server.py
   ```

5. **Verify it's working:**
   - You should see output like:
     ```
     📍 Local IP: 172.30.9.196
     🌐 Access at: http://172.30.9.196:5001
     📹 Stream URL: http://172.30.9.196:5001/video
     ```
   - Open `http://172.30.9.196:5001` in your browser to see the camera preview

6. **Keep this terminal open** - the server must stay running!

### Step 2: On Your Raspberry Pi

1. **Transfer the updated config** (already done):
   - The `config/config.json` file is now configured to use:
     ```json
     "camera_ip": "http://172.30.9.196:5001/video"
     ```

2. **Make sure both devices are on the same network:**
   - Laptop: Connected to your WiFi
   - Pi: Connected to the same WiFi

3. **Test the connection from Pi:**
   ```bash
   curl -I http://172.30.9.196:5001/health
   ```
   Should return: `"status": "ok"`

4. **Start your attendance system on the Pi:**
   ```bash
   python app.py
   ```

---

## 🔧 Troubleshooting

### Camera Server Won't Start

**Issue:** Port 5001 already in use
```powershell
# Find what's using port 5001
netstat -ano | findstr :5001

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

### Pi Can't Connect to Laptop Camera

1. **Check Windows Firewall:**
   ```powershell
   # Allow incoming connections on port 5001
   New-NetFirewallRule -DisplayName "Camera Server" -Direction Inbound -LocalPort 5001 -Protocol TCP -Action Allow
   ```

2. **Verify both devices are on same network:**
   ```powershell
   # On laptop - check your IP
   ipconfig
   
   # On Pi - try to ping laptop
   ping 172.30.9.196
   ```

3. **Test the stream URL directly:**
   - On Pi, open a browser: `http://172.30.9.196:5001`
   - You should see the camera preview page

### IP Address Changed

If your laptop's IP address changes (after restart or network change):

1. **Find new IP:**
   ```powershell
   ipconfig
   # Look for "IPv4 Address" under your WiFi adapter
   ```

2. **Update config.json:**
   - Change `camera_ip` and `camera_choice` to new IP
   - Example: `http://NEW_IP:5001/video`

3. **Restart camera server** on laptop

---

## 🎥 Camera Server Features

### Web Interface
- Access `http://YOUR_LAPTOP_IP:5001` for:
  - Live camera preview
  - Stream URL information
  - Setup instructions
  - Connection status

### Endpoints
- `/` - Home page with preview
- `/video` - Raw MJPEG stream (use this in config)
- `/health` - Health check endpoint

### Performance
- Stream quality: 85% JPEG quality
- Resolution: 640x480
- Frame rate: Up to 30 FPS
- Auto-reconnect support

---

## ⚙️ Advanced Configuration

### Change Camera Resolution

Edit `laptop_camera_server.py`:
```python
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)   # Change from 640
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)    # Change from 480
```

### Change Port

Edit `laptop_camera_server.py`:
```python
app.run(host='0.0.0.0', port=8080, ...)  # Change from 5001
```

Then update config.json with new port.

### Use Different Camera

If your laptop has multiple cameras:
```python
camera = cv2.VideoCapture(1)  # Change from 0 to 1, 2, etc.
```

---

## 💡 Tips

1. **Keep laptop plugged in** - streaming uses battery
2. **Disable sleep mode** - prevents camera disconnection
3. **Use stable WiFi** - wired connection is better if available
4. **Position laptop camera** - similar to where ESP32 was mounted

---

## 🔄 Switching Back to ESP32

When ESP32-CAM is fixed, update `config/config.json`:
```json
{
    "camera_ip": "http://192.168.4.1:81/stream",
    "camera_choice": "http://192.168.4.1:81/stream"
}
```

---

## 📝 Notes

- **Automatic on startup?** Add `laptop_camera_server.py` to Windows startup
- **Multiple cameras?** Run multiple servers on different ports
- **Remote access?** Use port forwarding (not recommended for security)
- **Better performance?** Consider using RTSP instead of MJPEG

---

## ✅ Quick Test Checklist

- [ ] Laptop camera server running
- [ ] Can access `http://172.30.9.196:5001` from laptop browser
- [ ] Pi can ping laptop IP (`172.30.9.196`)
- [ ] Pi can access camera stream URL
- [ ] Attendance system recognizes faces from laptop camera

---

**Status:** ✅ Camera configured at `http://172.30.9.196:5001/video`

**Last Updated:** December 18, 2025
