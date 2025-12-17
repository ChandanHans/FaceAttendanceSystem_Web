#!/usr/bin/env python3
"""
ESP32-CAM WiFi Configuration via GPIO UART
Reads WiFi credentials from config.json and sends them to ESP32-CAM via Raspberry Pi GPIO pins
No USB connection needed!
"""

import json
import serial
import time
import sys
import os

def load_config():
    """Load WiFi credentials from config.json"""
    try:
        with open('config/config.json', 'r') as f:
            config = json.load(f)
        return config.get('wifi_ssid'), config.get('wifi_password')
    except Exception as e:
        print(f"❌ Error reading config.json: {e}")
        return None, None

def configure_esp32_gpio(ssid, password):
    """Send WiFi credentials to ESP32-CAM via GPIO UART"""
    
    # Raspberry Pi serial port (GPIO 14 TX, GPIO 15 RX)
    SERIAL_PORT = '/dev/serial0'  # or /dev/ttyAMA0 on older Pi models
    BAUD_RATE = 9600
    
    try:
        print(f"\n📡 Opening GPIO UART: {SERIAL_PORT}")
        print("   Make sure UART is enabled: sudo raspi-config → Interface → Serial")
        print("   - Disable serial login shell: NO")
        print("   - Enable serial hardware: YES")
        
        # Open serial port
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=5)
        time.sleep(1)  # Wait for connection to stabilize
        
        # Send configuration command
        config_cmd = f"WIFI_CONFIG:{ssid}:{password}:\n"
        print(f"\n📤 Sending WiFi credentials...")
        print(f"   SSID: {ssid}")
        print(f"   Password: {'*' * len(password)}")
        
        ser.write(config_cmd.encode())
        ser.flush()
        
        # Wait for response
        print("\n📥 Waiting for ESP32 response...")
        start_time = time.time()
        response_received = False
        
        while time.time() - start_time < 10:  # 10 second timeout
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"   {line}")
                    if "CONFIGURED" in line:
                        response_received = True
                        break
        
        ser.close()
        
        if response_received:
            print("\n✅ Configuration successful!")
            return True
        else:
            print("\n⚠️  No confirmation received, but credentials sent.")
            print("   Check ESP32 Serial Monitor (115200 baud) for status")
            return True
            
    except serial.SerialException as e:
        print(f"\n❌ Serial port error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Enable UART: sudo raspi-config → Interface Options → Serial Port")
        print("      - Serial login shell: NO")
        print("      - Serial hardware: YES")
        print("   2. Check wiring:")
        print("      Pi GPIO14 (TX) → ESP32 GPIO12 (RX)")
        print("      Pi GPIO15 (RX) → ESP32 GPIO13 (TX)")
        print("      Pi GND → ESP32 GND")
        print("   3. Reboot Pi: sudo reboot")
        print("   4. Check port exists: ls -l /dev/serial*")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("ESP32-CAM WiFi Configuration via Raspberry Pi GPIO")
    print("=" * 70)
    
    # Check if running on Raspberry Pi
    if not os.path.exists('/dev/serial0') and not os.path.exists('/dev/ttyAMA0'):
        print("\n⚠️  This script is designed for Raspberry Pi GPIO UART")
        print("   Serial ports /dev/serial0 or /dev/ttyAMA0 not found")
        print("\n💡 If on Windows, use: python configure_esp32_wifi.py (USB version)")
        sys.exit(1)
    
    # Load credentials from config.json
    ssid, password = load_config()
    
    if not ssid or not password:
        print("❌ WiFi credentials not found in config.json")
        print("\nPlease add to config/config.json:")
        print('  "wifi_ssid": "YourWiFiName",')
        print('  "wifi_password": "YourPassword",')
        sys.exit(1)
    
    print(f"\n📋 WiFi Credentials from config.json:")
    print(f"   SSID: {ssid}")
    print(f"   Password: {'*' * len(password)}")
    
    print("\n" + "=" * 70)
    print("🔌 GPIO Wiring Check:")
    print("=" * 70)
    print("   Pi GPIO14 (TX, Pin 8)  → ESP32-CAM GPIO12 (RX)")
    print("   Pi GPIO15 (RX, Pin 10) → ESP32-CAM GPIO13 (TX)")
    print("   Pi GND (Pin 6, 9, etc) → ESP32-CAM GND")
    print("   Pi 5V (Pin 2 or 4)     → ESP32-CAM 5V")
    print("=" * 70)
    
    input("\n⚠️  Press ENTER to send configuration to ESP32-CAM...")
    
    success = configure_esp32_gpio(ssid, password)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ Configuration Complete!")
        print("=" * 70)
        print("\n📝 Next Steps:")
        print("1. Press RESET button on ESP32-CAM")
        print("2. Check USB Serial Monitor (115200 baud) for connection status")
        print("3. ESP32 will display its IP address")
        print("4. Stream URL: http://<ESP32_IP>:81/stream")
        print("\n💡 To change WiFi later:")
        print("   - Edit config/config.json")
        print("   - Run this script again")
        print("   - Press RESET on ESP32")
    else:
        print("\n❌ Configuration failed. Check wiring and UART settings.")
        sys.exit(1)

if __name__ == "__main__":
    main()
