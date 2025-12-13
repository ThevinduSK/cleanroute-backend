# Device WiFi Setup Guide

## Hardware Component Setup Flow

### Option 1: AP Mode Configuration (Recommended)
**Best for: Easy user setup without extra hardware**

#### How it works:
1. **First Boot** → Device creates WiFi Access Point
   - SSID: `CleanRoute-Setup-{BIN_ID}`
   - Password: Printed on device sticker
2. **User connects** phone to this AP
3. **Captive portal** opens automatically (or browse to `192.168.4.1`)
4. **User enters**:
   - Home WiFi SSID & Password
   - User ID / Phone number
   - Device location (optional, can use GPS)
5. **Device saves** config and reboots
6. **Connects** to home WiFi
7. **Sends registration** message to backend

#### ESP32 Code Snippet:
```cpp
#include <WiFi.h>
#include <WebServer.h>

const char* ap_ssid = "CleanRoute-Setup-B001";
const char* ap_password = "cleanroute";

WebServer server(80);

void setup() {
    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP(ap_ssid, ap_password);
    
    server.on("/", handleRoot);  // Show config form
    server.on("/save", handleSave);  // Save WiFi credentials
    server.begin();
}
```

---

### Option 2: Small OLED Display + Buttons
**Best for: No smartphone needed, physical control**

#### How it works:
1. Device has small OLED (0.96" 128x64) + 3 buttons
2. **Setup Mode**:
   - Scan for WiFi networks
   - Use buttons to scroll & select
   - Enter password using on-screen keyboard
3. **Display shows**:
   - Current status (online/offline)
   - Last telemetry sent
   - Battery level
4. **Button actions**:
   - Button 1: Up/scroll
   - Button 2: Down/select
   - Button 3: Menu/back

---

### Option 3: Bluetooth LE + Mobile App
**Best for: Modern, app-based experience**

#### How it works:
1. Device advertises BLE service: `CleanRoute-B001`
2. User downloads CleanRoute mobile app
3. App scans for nearby devices
4. User pairs with device via BLE
5. App sends WiFi credentials + user profile via BLE
6. Device saves and connects to WiFi

---

## Recommended Solution: **AP Mode (Option 1)**

### Why?
- No extra hardware (OLED/buttons) needed
- Works with any smartphone
- Intuitive web interface
- Can capture user details easily
- Cost-effective

### Hardware Required:
- ESP32 (built-in WiFi)
- Weight sensor (HX711 + Load cell)
- Power supply (battery + solar)
- Waterproof enclosure
- Sticker with QR code + AP password

---

## User Registration Flow

### Step 1: Physical Setup
```
User receives device
    ↓
Attach to bin (magnets or screws)
    ↓
Power on device
    ↓
Device LED blinks blue (AP mode active)
```

### Step 2: WiFi Configuration
```
User scans QR code → Opens instructions
    ↓
Connect to "CleanRoute-Setup-B001"
    ↓
Captive portal opens automatically
    ↓
Enter WiFi credentials + user info
    ↓
Submit → Device saves and reboots
    ↓
Device LED turns green (connected)
```

### Step 3: Backend Registration
```
Device sends registration message:
Topic: cleanroute/bins/B001/register
Payload: {
    "bin_id": "B001",
    "user_id": "USER123",
    "user_name": "John Doe",
    "user_phone": "+94771234567",
    "wifi_ssid": "MyHomeWiFi",
    "lat": 6.9271,
    "lon": 79.8612
}
    ↓
Backend stores in database
    ↓
Backend sends confirmation command
    ↓
User receives SMS/app notification: "Device registered!"
```

---

## Collection Day Workflow

### Municipal Operator View (Web Dashboard)

```
1. Login to dashboard
2. Click "Start Collection Day"
3. System:
   - Broadcasts wake_up command to all bins
   - Creates alerts for all users
   - Starts monitoring responses
4. Dashboard shows:
   - Total bins: 50
   - Online: 45
   - Offline: 5 (show user names)
5. Click "Send Reminders" for offline bins
6. View real-time fill levels on map
7. End of day: Click "End Collection"
   - All bins go to sleep mode
```

### User Experience

```
Day 1 (Setup):
    - Install device
    - Configure WiFi
    - Device sleeps (0.5mA consumption)

Collection Day Morning (8 AM):
    - Receive SMS: "Collection today! Please ensure bin device is on."
    - Device wakes up automatically
    - Sends telemetry every hour
    - User doesn't need to do anything if device is working

Evening (8 PM):
    - Collection complete
    - Device receives sleep command
    - Back to low power mode
```

---

## Power Management

### Normal Operation (Non-Collection Days)
```cpp
// Deep sleep most of the time
esp_sleep_enable_timer_wakeup(24 * 60 * 60 * 1000000); // 24 hours
esp_deep_sleep_start();
```

### Collection Day
```cpp
// Wake up, send telemetry, light sleep
sendTelemetry();
esp_sleep_enable_timer_wakeup(60 * 60 * 1000000); // 1 hour
esp_light_sleep_start();
```

### Battery Life Estimate:
- **Normal days**: 0.5mA average → ~2 years on 3000mAh battery
- **Collection day**: 50mA average for 12 hours → 600mAh per collection
- **With solar**: Indefinite (100mA panel charges during day)

---

## API Endpoints for Device Setup

### 1. Register Device
```bash
POST /devices/register
{
    "bin_id": "B001",
    "user_id": "USER123",
    "user_name": "John Doe",
    "user_phone": "+94771234567",
    "wifi_ssid": "MyHomeWiFi",
    "lat": 6.9271,
    "lon": 79.8612
}
```

### 2. Check User's Devices
```bash
GET /devices/user/USER123
```

### 3. Get Device Health
```bash
GET /devices/B001/health
```

---

## Complete Device Code Template

See `device_firmware/` directory for:
- `esp32_wifi_setup.ino` - AP mode setup
- `esp32_main.ino` - Main firmware with MQTT
- `esp32_power_mgmt.ino` - Sleep/wake logic
