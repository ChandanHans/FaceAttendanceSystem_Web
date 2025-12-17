# ESP32-CAM WiFi Configuration Guide

## Overview
Your ESP32-CAM can now be configured using WiFi credentials stored in `config/config.json`. No need to modify Arduino code!

---

## 📋 Setup Steps

### 1. Edit WiFi Credentials
Edit `config/config.json` and update:
```json
{
    "wifi_ssid": "YourWiFiName",
    "wifi_password": "YourPassword",
    ...
}
```

### 2. Upload Arduino Code (One-Time)
1. Open `ESP32_CAM_Code.ino` in Arduino IDE
2. Upload to ESP32-CAM
3. This step only needs to be done once!

### 3. Configure WiFi Credentials

#### **On Raspberry Pi:**
```bash
python3 configure_esp32_wifi.py
```

#### **On Windows:**
```bash
python configure_esp32_wifi.py
```

The script will:
- Read credentials from `config/config.json`
- Auto-detect ESP32-CAM USB port
- Send credentials to ESP32
- Save them to ESP32's permanent memory (EEPROM)

### 4. Reset ESP32-CAM
Press the **RESET** button on the ESP32-CAM

### 5. Check Connection
The ESP32 will:
- Connect to your WiFi
- Display its IP address in Serial Monitor
- Start streaming at `http://<IP>:81/stream`

---

## 🔄 Changing WiFi Later

1. Edit `config/config.json` with new credentials
2. Connect ESP32-CAM via USB
3. Run `python configure_esp32_wifi.py`
4. Press RESET on ESP32-CAM

**No need to re-upload Arduino code!**

---

## 🛠️ How It Works

```
config.json → Python Script → Serial USB → ESP32 EEPROM
                                              ↓
                                         WiFi Connect
```

1. **config.json**: Stores credentials for easy editing
2. **Python script**: Reads config and sends to ESP32
3. **ESP32 EEPROM**: Permanently stores credentials (survives power-off)
4. **Auto-connect**: ESP32 automatically connects on boot

---

## ❓ Troubleshooting

### ESP32 Not Found
```bash
# On Windows: Check Device Manager → Ports (COM & LPT)
# Common ports: COM3, COM4, COM5

# Manually specify port:
python configure_esp32_wifi.py
# When prompted, enter: COM3 (or your port)
```

### Connection Failed
1. Check Serial Monitor (115200 baud) for error messages
2. Verify SSID/password are correct in `config.json`
3. Make sure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
4. Press RESET button after configuration

### Wrong Credentials Saved
Run the configuration script again with correct credentials in `config.json`

---

## 📦 Requirements

**Python packages:**
```bash
pip install pyserial
```

**Hardware:**
- ESP32-CAM connected via USB-to-Serial adapter (FTDI/CH340)
- USB cable connected to computer

---

## 🔍 Serial Monitor Output

When ESP32 boots, you'll see:
```
========================================
ESP32-CAM Configurable WiFi
========================================

⏳ Waiting for WiFi configuration...
   (Send via Python script or press RESET to use saved/default)

✅ Loaded WiFi config from EEPROM

📡 WiFi Credentials:
   SSID: YourWiFiName
   Password: ********

🔌 Connecting to WiFi...
...
✅ WiFi Connected!
   ESP32-CAM IP: 192.168.1.100

========================================
✅ Camera Ready!
========================================
📹 Stream URL: http://192.168.1.100:81/stream

💡 To change WiFi:
   1. Edit config/config.json on Pi
   2. Run: python configure_esp32_wifi.py
   3. Press RESET on ESP32
========================================
```

---

## 🎯 Benefits

✅ **No code editing**: Update WiFi without modifying Arduino code  
✅ **Easy deployment**: Configure multiple ESP32 devices quickly  
✅ **Persistent**: Credentials saved permanently in EEPROM  
✅ **Fallback**: Uses default credentials if EEPROM is empty  
✅ **User-friendly**: Simple Python script does all the work

---

## 📝 Default Credentials

If EEPROM is empty, ESP32 uses these defaults:
- **SSID**: `FaceAttendance-Pi`
- **Password**: `attendance2025`

Configure via Python script to override!
