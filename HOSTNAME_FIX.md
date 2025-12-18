# Fix hostname.local Not Working

## Problem
`raspberrypi.local:5000` or `hostname.local` not working when accessing from laptop.

## Root Cause
The issue is **NOT** related to serial port settings. It's an **mDNS (Avahi)** problem.

Serial port settings are only for ESP32 GPIO communication - they don't affect network hostname resolution.

---

## Solution: Install and Enable Avahi on Raspberry Pi

### 1. Install Avahi Daemon
```bash
sudo apt update
sudo apt install avahi-daemon avahi-utils -y
```

### 2. Enable and Start Avahi
```bash
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
```

### 3. Verify Avahi is Running
```bash
sudo systemctl status avahi-daemon
```

Should show: `Active: active (running)`

### 4. Check Hostname
```bash
hostname
# Output: raspberrypi (or your custom hostname)

avahi-browse -a -t
# Should list services including _workstation._tcp
# Example output:
# +  wlan0 IPv4 chandan-2 [2c:cf:67:46:a2:eb]  Workstation  local
# Note: If you see "chandan-2" instead of "chandan", use "chandan-2.local"
# The -2 suffix means there's a hostname conflict on your network
```

### 5. Test from Laptop
```bash
# Windows PowerShell:
ping raspberrypi.local

# Should respond with IP like: 192.168.1.100
```

---

## Windows-Side Fix (If Still Not Working)

### Install Bonjour Service
Download and install: [Apple Bonjour Print Services](https://support.apple.com/kb/DL999)

Or install iTunes (includes Bonjour automatically).

**After installation:**
- Restart Windows
- Try `ping raspberrypi.local` again

---

## Alternative: Use IP Discovery Script

If hostname.local still doesn't work, use this script to auto-discover Pi:

**Create `find_pi.py`:**
```python
import socket
import subprocess

def find_raspberry_pi():
    """Auto-discover Raspberry Pi on network"""
    try:
        # Try hostname.local first
        ip = socket.gethostbyname('raspberrypi.local')
        print(f"✅ Found Pi at: {ip}")
        return ip
    except:
        print("⚠️ hostname.local not working, scanning network...")
        
    # Fallback: scan local network
    try:
        # Get local IP range
        result = subprocess.check_output(['arp', '-a'], text=True)
        print("📡 Scanning network for Raspberry Pi...")
        # Look for common Pi MAC address patterns
        # (This is a simplified version - real implementation would be more robust)
        return None
    except:
        return None

if __name__ == "__main__":
    ip = find_raspberry_pi()
    if ip:
        print(f"\n🌐 Access webapp at: http://{ip}:5000")
    else:
        print("\n❌ Could not find Raspberry Pi")
        print("Please check:")
        print("1. Pi is powered on")
        print("2. Pi is connected to same network")
        print("3. Avahi daemon is running on Pi")
```

---

## Update Config to Use Hostname

**Edit `config/config.json`:**
```json
{
    "camera_choice": "http://raspberrypi.local:81/stream",
    ...
}
```

This way:
- ✅ No need to update IP each time
- ✅ Works even if Pi gets different IP from DHCP
- ✅ Survives router reboots

---

## Fix Hostname Conflict (chandan vs chandan-2)

If `avahi-browse -a -t` shows `chandan-2` instead of `chandan`, there are two options:

### Quick Fix: Just Use chandan-2.local
Access your Pi with:
```
http://chandan-2.local:5000
```
Update your config to use `chandan-2.local` instead of `chandan.local`.

### Permanent Fix: Change to Unique Hostname

There's another device on your network using "chandan". Change your Pi's hostname to something unique:

```bash
# Change hostname
sudo hostnamectl set-hostname attendance-pi

# Restart Avahi
sudo systemctl restart avahi-daemon

# Verify
avahi-browse -a -t
# Should now show: attendance-pi (without -2)
```

Now access via: `http://attendance-pi.local:5000`

---

## Set Static Hostname on Pi

**Edit hostname:**
```bash
sudo nano /etc/hostname
```
Change `raspberrypi` to something unique like `attendance-pi`

**Edit hosts:**
```bash
sudo nano /etc/hosts
```
Change `raspberrypi` to `attendance-pi`

**Reboot:**
```bash
sudo reboot
```

Now access via: `http://attendance-pi.local:5000`

---

## Static IP Alternative (More Reliable)

If mDNS is unreliable, set a static IP on Pi:

**Edit dhcpcd.conf:**
```bash
sudo nano /etc/dhcpcd.conf
```

**Add at the end:**
```
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

**Reboot:**
```bash
sudo reboot
```

Now always access via: `http://192.168.1.100:5000`

---

## Quick Diagnosis

### On Raspberry Pi:
```bash
# Check Avahi is running
sudo systemctl status avahi-daemon

# Check if hostname is advertised
avahi-browse -a -t | grep -i workstation

# Check network interface
ip addr show wlan0
```

### On Windows Laptop:
```bash
# Test mDNS resolution
ping raspberrypi.local

# If fails, check Bonjour service
services.msc
# Look for "Bonjour Service" - should be Running
```

---

## Why This Happens

1. **Avahi not installed** - Pi doesn't advertise its hostname
2. **Windows lacks mDNS** - Needs Bonjour/iTunes to resolve .local names
3. **Firewall blocking** - Port 5353 (mDNS) might be blocked
4. **Different subnets** - Pi and laptop on different networks

---

## Summary

✅ **Install Avahi on Pi** (primary fix)  
✅ **Install Bonjour on Windows** (if needed)  
✅ **Use static IP as backup** (most reliable)  
❌ **Serial port settings are irrelevant** (only for ESP32 GPIO)

The serial port configuration in `raspi-config` is only for:
- ESP32-CAM GPIO communication
- Serial console login (disabled)
- UART hardware enable (enabled)

It has **ZERO** effect on network/hostname resolution!
