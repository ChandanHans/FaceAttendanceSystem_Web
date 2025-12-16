#!/bin/bash
# Setup Raspberry Pi 5 as WiFi Hotspot for ESP32-CAM
# The Pi will create a hotspot while connected to internet via WiFi or Ethernet

echo "========================================="
echo "Setting up Pi 5 as WiFi Hotspot"
echo "========================================="
echo ""

# Install required packages
echo "📦 Installing NetworkManager..."
sudo apt-get update
sudo apt-get install -y network-manager

# Stop and disable dhcpcd (conflicts with NetworkManager)
echo "🔧 Configuring network services..."
sudo systemctl stop dhcpcd
sudo systemctl disable dhcpcd
sudo systemctl enable NetworkManager
sudo systemctl start NetworkManager

echo ""
echo "⚙️  Creating hotspot configuration..."
echo ""

# Hotspot settings
HOTSPOT_SSID="FaceAttendance-Pi"
HOTSPOT_PASSWORD="attendance2025"
HOTSPOT_IP="10.42.0.1"

# Create hotspot connection
sudo nmcli connection add type wifi ifname wlan0 con-name Hotspot autoconnect yes ssid "$HOTSPOT_SSID"
sudo nmcli connection modify Hotspot 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
sudo nmcli connection modify Hotspot wifi-sec.key-mgmt wpa-psk
sudo nmcli connection modify Hotspot wifi-sec.psk "$HOTSPOT_PASSWORD"

# Set static IP for hotspot
sudo nmcli connection modify Hotspot ipv4.addresses $HOTSPOT_IP/24

echo ""
echo "========================================="
echo "✅ Hotspot Setup Complete!"
echo "========================================="
echo ""
echo "📡 Hotspot Details:"
echo "   SSID: $HOTSPOT_SSID"
echo "   Password: $HOTSPOT_PASSWORD"
echo "   Pi IP: $HOTSPOT_IP"
echo ""
echo "🔧 ESP32-CAM Configuration:"
echo "   In Arduino code, set:"
echo "   const char* ssid = \"$HOTSPOT_SSID\";"
echo "   const char* password = \"$HOTSPOT_PASSWORD\";"
echo ""
echo "📝 The ESP32-CAM will get IP: 10.42.0.X"
echo "   Stream URL: http://10.42.0.X:81/stream"
echo ""
echo "🌐 To activate hotspot:"
echo "   sudo nmcli connection up Hotspot"
echo ""
echo "🌐 To connect Pi to WiFi (for internet):"
echo "   sudo nmcli device wifi connect \"YOUR_WIFI\" password \"YOUR_PASSWORD\""
echo ""
echo "🔄 Or use: sudo raspi-config → Network Options → Connect to WiFi"
echo ""
echo "Note: Hotspot auto-starts on boot"
echo "Reboot now for changes to take effect"
echo ""

read -p "Reboot now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi
