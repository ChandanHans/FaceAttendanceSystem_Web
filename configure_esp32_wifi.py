#!/usr/bin/env python3
"""
ESP32-CAM WiFi Configuration Script
Reads WiFi credentials from config.json and sends them to ESP32-CAM via serial
"""

import json
import serial
import serial.tools.list_ports
import time
import sys

def load_config():
    """Load WiFi credentials from config.json"""
    try:
        with open('config/config.json', 'r') as f:
            config = json.load(f)
        return config.get('wifi_ssid'), config.get('wifi_password')
    except Exception as e:
        print(f"❌ Error reading config.json: {e}")
        return None, None

def find_esp32_port():
    """Find ESP32 serial port automatically"""
    print("🔍 Searching for ESP32-CAM...")
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        # ESP32 typically shows as CH340, CP210x, or similar
        if any(keyword in port.description.upper() for keyword in ['CH340', 'CP210', 'UART', 'USB-SERIAL', 'USB SERIAL']):
            print(f"✅ Found potential ESP32 at: {port.device}")
            return port.device
    
    print("\n⚠️  Could not auto-detect ESP32. Available ports:")
    for port in ports:
        print(f"   - {port.device}: {port.description}")
    
    return None

def configure_esp32(port, ssid, password):
    """Send WiFi credentials to ESP32-CAM via serial"""
    try:
        print(f"\n📡 Connecting to ESP32-CAM on {port}...")
        ser = serial.Serial(port, 115200, timeout=5)
        time.sleep(2)  # Wait for connection to stabilize
        
        print("⏳ Waiting for ESP32 to be ready...")
        time.sleep(1)
        
        # Send configuration command
        config_cmd = f"WIFI_CONFIG:{ssid}:{password}\n"
        print(f"📤 Sending: SSID='{ssid}', Password='{password}'")
        
        ser.write(config_cmd.encode())
        ser.flush()
        
        # Read response
        print("\n📥 ESP32 Response:")
        start_time = time.time()
        while time.time() - start_time < 10:  # 10 second timeout
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"   {line}")
                    if "CONFIGURED" in line or "Connected" in line:
                        print("\n✅ Configuration successful!")
                        ser.close()
                        return True
        
        ser.close()
        print("\n⚠️  No confirmation received, but credentials sent.")
        return True
        
    except serial.SerialException as e:
        print(f"❌ Serial port error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("ESP32-CAM WiFi Configuration Tool")
    print("=" * 60)
    
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
    
    # Find ESP32 port
    port = find_esp32_port()
    
    if not port:
        port = input("\n❓ Enter COM port manually (e.g., COM3): ").strip()
        if not port:
            print("❌ No port specified. Exiting.")
            sys.exit(1)
    
    # Configure ESP32
    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT:")
    print("1. Make sure ESP32-CAM is connected via USB")
    print("2. Press RESET button on ESP32 after this script runs")
    print("3. ESP32 will connect to WiFi and show its IP address")
    print("=" * 60)
    
    input("\nPress ENTER to configure ESP32-CAM...")
    
    success = configure_esp32(port, ssid, password)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Configuration Complete!")
        print("=" * 60)
        print("\n📝 Next Steps:")
        print("1. Press RESET button on ESP32-CAM")
        print("2. Open Serial Monitor to see connection status")
        print("3. ESP32 will display its IP address")
        print("4. Stream URL: http://<ESP32_IP>:81/stream")
    else:
        print("\n❌ Configuration failed. Please try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
