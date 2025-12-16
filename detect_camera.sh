#!/bin/bash
# WiFi Camera Detection and Configuration Script

echo "========================================="
echo "WiFi Camera Detection for Raspberry Pi"
echo "========================================="
echo ""

echo "🔍 Scanning network for devices..."
echo ""

# Get local IP and subnet
LOCAL_IP=$(hostname -I | awk '{print $1}')
SUBNET=$(echo $LOCAL_IP | cut -d. -f1-3)

echo "📍 Your Pi IP: $LOCAL_IP"
echo "🌐 Scanning subnet: $SUBNET.0/24"
echo ""

# Install nmap if not present
if ! command -v nmap &> /dev/null; then
    echo "📦 Installing nmap..."
    sudo apt-get update -qq
    sudo apt-get install -y nmap
fi

echo "⏳ Scanning for devices (this takes 1-2 minutes)..."
sudo nmap -sn $SUBNET.0/24 | grep -B 2 "Host is up" | grep "Nmap scan" | awk '{print $5}'

echo ""
echo "========================================="
echo "Common WiFi Camera Ports:"
echo "========================================="
echo "RTSP: 554, 8554"
echo "HTTP: 80, 8080, 8081"
echo "ONVIF: 8000, 8080"
echo ""

read -p "Enter camera IP address to test (e.g., 192.168.1.100): " CAMERA_IP

if [ -z "$CAMERA_IP" ]; then
    echo "❌ No IP provided. Exiting."
    exit 1
fi

echo ""
echo "🔍 Scanning camera at $CAMERA_IP..."
nmap -p 554,8554,80,8080,8081,8000 $CAMERA_IP

echo ""
echo "========================================="
echo "Testing Camera Streams"
echo "========================================="
echo ""

# Common RTSP paths
RTSP_PATHS=(
    "rtsp://$CAMERA_IP:554/stream1"
    "rtsp://$CAMERA_IP:554/stream"
    "rtsp://$CAMERA_IP:554/live"
    "rtsp://$CAMERA_IP:554/h264"
    "rtsp://$CAMERA_IP:8554/stream1"
    "rtsp://$CAMERA_IP/onvif1"
    "rtsp://$CAMERA_IP/cam/realmonitor?channel=1&subtype=0"
)

HTTP_PATHS=(
    "http://$CAMERA_IP:8080/video"
    "http://$CAMERA_IP:8081/video"
    "http://$CAMERA_IP/video"
    "http://$CAMERA_IP/mjpeg"
)

echo "Testing RTSP streams (5 seconds each)..."
for path in "${RTSP_PATHS[@]}"; do
    echo -n "Testing: $path ... "
    timeout 5 ffmpeg -rtsp_transport tcp -i "$path" -frames:v 1 -f null - >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ SUCCESS"
        WORKING_STREAM="$path"
        break
    else
        echo "❌"
    fi
done

if [ -z "$WORKING_STREAM" ]; then
    echo ""
    echo "RTSP streams failed. Trying HTTP..."
    for path in "${HTTP_PATHS[@]}"; do
        echo -n "Testing: $path ... "
        timeout 3 curl -s -o /dev/null -w "%{http_code}" "$path" | grep -q "200"
        if [ $? -eq 0 ]; then
            echo "✅ SUCCESS"
            WORKING_STREAM="$path"
            break
        else
            echo "❌"
        fi
    done
fi

echo ""
echo "========================================="
echo "Results"
echo "========================================="
echo ""

if [ -n "$WORKING_STREAM" ]; then
    echo "✅ Working stream found!"
    echo "📹 Stream URL: $WORKING_STREAM"
    echo ""
    echo "To use this camera, update config/config.json:"
    echo ""
    echo "{"
    echo "  \"camera_choice\": 0,"
    echo "  \"camera_ip\": \"$WORKING_STREAM\","
    echo "  ..."
    echo "}"
    echo ""
    
    read -p "Would you like to update config.json now? (y/n): " UPDATE_CONFIG
    if [[ $UPDATE_CONFIG =~ ^[Yy]$ ]]; then
        python3 -c "
import json
try:
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    config['camera_ip'] = '$WORKING_STREAM'
    with open('config/config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print('✅ Config updated successfully!')
except Exception as e:
    print(f'❌ Failed to update config: {e}')
"
    fi
else
    echo "❌ No working stream found automatically."
    echo ""
    echo "📝 Manual configuration required:"
    echo ""
    echo "1. Check your camera's manual for RTSP URL format"
    echo "2. Common formats:"
    echo "   - rtsp://username:password@$CAMERA_IP:554/stream1"
    echo "   - rtsp://$CAMERA_IP:554/live"
    echo "   - http://$CAMERA_IP:8080/video"
    echo ""
    echo "3. If your camera requires credentials:"
    echo "   rtsp://admin:password@$CAMERA_IP:554/stream1"
    echo ""
    echo "4. Use VLC to test: vlc rtsp://your-camera-url"
    echo ""
    echo "5. Update config/config.json with working URL"
fi

echo ""
echo "📚 For more help, check your camera manufacturer's documentation"
echo "   Common brands: Hikvision, Dahua, TP-Link, Yi, Wyze"
echo ""
