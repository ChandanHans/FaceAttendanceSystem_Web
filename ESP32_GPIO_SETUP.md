# ESP32-CAM WiFi Configuration via GPIO (No USB!)

## Overview
Configure ESP32-CAM WiFi credentials from Raspberry Pi using GPIO pins directly. **No USB cable needed** between Pi and ESP32!

---

## 🔌 GPIO Wiring

### Connection Diagram:
```
Raspberry Pi          ESP32-CAM AI Thinker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pin 2 (5V)      →    5V
Pin 6 (GND)     →    GND
Pin 8 (GPIO14 TX) →  GPIO12 (RX)
Pin 10(GPIO15 RX) →  GPIO13 (TX)
```

### Physical Pin Layout:

**Raspberry Pi (40-pin header):**
```
   3V3  (1) (2)  5V  ← Connect to ESP32 5V
 GPIO2  (3) (4)  5V
 GPIO3  (5) (6)  GND ← Connect to ESP32 GND
 GPIO4  (7) (8)  GPIO14 (TX) ← Connect to ESP32 GPIO12
   GND  (9) (10) GPIO15 (RX) ← Connect to ESP32 GPIO13
```

**ESP32-CAM AI Thinker:**
```
5V  ←─ Pi Pin 2 (5V)
GND ←─ Pi Pin 6 (GND)
IO12 ←─ Pi Pin 8 (GPIO14 TX)
IO13 ←─ Pi Pin 10 (GPIO15 RX)
```

### Wire Colors (suggested):
- **Red**: 5V
- **Black**: GND  
- **Yellow/Orange**: TX (Pi GPIO14 → ESP32 GPIO12)
- **Green/Blue**: RX (Pi GPIO15 → ESP32 GPIO13)

---

## ⚙️ Raspberry Pi UART Setup

### 1. Enable UART Hardware
```bash
sudo raspi-config
```

Navigate to:
- **Interface Options** → **Serial Port**
- "Would you like a login shell accessible over serial?" → **NO**
- "Would you like the serial port hardware enabled?" → **YES**

### 2. Verify UART is Available
```bash
ls -l /dev/serial*
# Should show: /dev/serial0 -> /dev/ttyAMA0
```

### 3. Reboot Pi
```bash
sudo reboot
```

---

## 🚀 Usage Steps

### 1. Edit WiFi Credentials
Edit `config/config.json`:
```json
{
    "wifi_ssid": "YourWiFiName",
    "wifi_password": "YourPassword",
    ...
}
```

### 2. Upload Arduino Code (One-Time)
1. Open `ESP32_CAM_Code.ino` in Arduino IDE
2. Upload via USB (FTDI/CH340 adapter)
3. **Only needs to be done once!**

### 3. Connect GPIO Wires
Follow the wiring diagram above. **Double-check connections!**

### 4. Power On ESP32-CAM
The ESP32 is now powered by Pi's 5V pin (or separate power supply).

### 5. Run Configuration Script
```bash
cd /path/to/FaceAttendanceSystem_Web
python3 configure_esp32_gpio.py
```

### 6. Press RESET on ESP32-CAM
ESP32 will connect to WiFi and start streaming!

---

## 📺 Monitoring

### View ESP32 Status (Optional)
Connect USB-Serial adapter to ESP32 for debugging:
```bash
# On Pi:
sudo apt install minicom
minicom -b 115200 -D /dev/ttyUSB0

# On Windows:
# Use Arduino Serial Monitor at 115200 baud
```

You'll see:
```
========================================
ESP32-CAM Configurable WiFi (GPIO UART)
========================================
📡 GPIO UART: RX=12, TX=13

⏳ Waiting for WiFi configuration from Pi...

✅ Loaded WiFi config from EEPROM
📡 WiFi Credentials:
   SSID: YourWiFiName
   Password: ********

🔌 Connecting to WiFi...
✅ WiFi Connected!
   ESP32-CAM IP: 192.168.1.100

✅ Camera Ready!
📹 Stream URL: http://192.168.1.100:81/stream
```

---

## 🔄 Changing WiFi Later

1. Edit `config/config.json` with new credentials
2. Run: `python3 configure_esp32_gpio.py`
3. Press **RESET** on ESP32-CAM
4. Done! No re-upload needed!

---

## ❓ Troubleshooting

### "Serial port not found"
```bash
# Check UART is enabled:
ls -l /dev/serial*

# If not present:
sudo raspi-config
# Enable serial hardware, disable login shell
sudo reboot
```

### "Permission denied"
```bash
# Add user to dialout group:
sudo usermod -a -G dialout $USER
sudo reboot
```

### ESP32 Not Responding
1. **Check wiring** - Ensure TX→RX, RX→TX crossover
2. **Common ground** - Pi GND must connect to ESP32 GND
3. **Power** - ESP32-CAM needs **5V 2A** minimum
4. **Press RESET** after wiring changes

### WiFi Connection Failed
1. Check `config.json` credentials are correct
2. Ensure WiFi is **2.4GHz** (ESP32 doesn't support 5GHz)
3. Check ESP32 is in range of WiFi router
4. View Serial Monitor for error messages

---

## 💡 How It Works

```
config.json → Python Script → Pi GPIO UART → ESP32 GPIO UART → EEPROM
                                                                   ↓
                                                              WiFi Connect
```

1. **config.json**: User-editable WiFi credentials
2. **Python script**: Reads config, sends via Pi GPIO
3. **Pi GPIO UART**: GPIO14/15 hardware serial (9600 baud)
4. **ESP32 GPIO UART**: GPIO12/13 hardware serial (Serial2)
5. **EEPROM**: ESP32 stores credentials permanently
6. **Auto-connect**: ESP32 connects on every boot

---

## 🎯 Advantages Over USB

✅ **No USB cable needed** between Pi and ESP32  
✅ **Cleaner wiring** - just 4 wires (Power, GND, TX, RX)  
✅ **Permanent setup** - ESP32 stays connected to Pi  
✅ **Lower power** - No USB-to-Serial adapter needed  
✅ **Production ready** - Suitable for final deployment  

---

## 📦 Requirements

**Python packages:**
```bash
pip3 install pyserial
```

**Hardware:**
- Raspberry Pi (any model with 40-pin GPIO)
- ESP32-CAM AI Thinker
- 4 jumper wires (male-to-female)
- 5V power supply for ESP32 (2A minimum)

---

## 🔒 Security Note

WiFi credentials are:
- Stored in `config.json` (plaintext)
- Transmitted via GPIO UART (unencrypted)
- Stored in ESP32 EEPROM (unencrypted)

For production:
- Protect `config.json` with proper file permissions
- Consider encrypting sensitive data
- Use secure WiFi networks only

---

## 📸 Expected Results

After successful configuration:
- ✅ ESP32 connects to WiFi automatically
- ✅ Stream available at: `http://<ESP32_IP>:81/stream`
- ✅ Credentials persist across power cycles
- ✅ No USB connection needed for normal operation
- ✅ Easy reconfiguration via Python script

---

## 🛠️ Advanced: Manual Testing

Test GPIO UART manually:

**On Pi:**
```bash
# Send test message:
echo "WIFI_CONFIG:TestSSID:TestPass:" > /dev/serial0
```

**On ESP32 Serial Monitor:**
You should see:
```
📡 Received WiFi configuration:
   SSID: TestSSID
   Password: ********
✅ CONFIGURED
```

---

## 🔗 Related Files

- **Arduino Code**: `ESP32_CAM_Code.ino`
- **Python Script**: `configure_esp32_gpio.py`
- **Configuration**: `config/config.json`
- **USB Alternative**: `configure_esp32_wifi.py` (if you prefer USB)
