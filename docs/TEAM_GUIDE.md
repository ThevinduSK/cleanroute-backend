# CleanRoute AI - Team Collaboration Guide

## System Overview

CleanRoute is a smart waste bin monitoring system that helps municipal councils optimize garbage collection routes. The system consists of three main components:

1. **Hardware (Person 1)** - ESP32-based sensors attached to bins
2. **Backend (Person 2)** - Python/FastAPI server that processes data
3. **UI/ML (Person 3)** - Web dashboard and predictive analytics

## ✨ **NEW: ML Prediction & Route Optimization IMPLEMENTED!**

- EWMA-based fill prediction** - Predict future bin fill levels
- Greedy nearest-neighbor routing** - Generate optimal collection routes
- RESTful API endpoints** - Ready for frontend integration
- Configurable thresholds** - Adjust for different scenarios

📚 **Quick Start:** See `ML_ROUTING_QUICKREF.md` for API usage
📖 **Full Guide:** See `ML_ROUTING_GUIDE.md` for implementation details
- Testing:** Run `python backend/test_ml_routing.py`

**New API Endpoints:**
- `GET /bins/forecast` - Predict all bins at future time
- `GET /bins/{id}/prediction` - Predict single bin
- `POST /routes/optimize` - Generate optimal route ⭐

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              COMPLETE FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐      MQTT       ┌──────────────┐      REST      ┌──────┐ │
│  │   DEVICES    │ ───────────────>│   BACKEND    │ <─────────────>│  UI  │ │
│  │   (ESP32)    │ <───────────────│  (FastAPI)   │                │(React)│ │
│  └──────────────┘    Commands     └──────┬───────┘                └──────┘ │
│                                          │                                  │
│                                          ▼                                  │
│                                   ┌──────────────┐                          │
│                                   │  PostgreSQL  │                          │
│                                   │  (Database)  │                          │
│                                   └──────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 👷 For Hardware Team (Person 1)

### What Your Device Needs to Do

#### **Phase 1: Device Setup (One-Time)**

```
User powers ON the device
        ↓
Device creates WiFi Access Point
    SSID: "CleanRoute-Setup-B001"
    Password: printed on device sticker
        ↓
User connects phone to this WiFi
        ↓
Captive portal opens automatically (192.168.4.1)
        ↓
User enters:
    • Home WiFi name & password
    • Their name & phone number
    • Bin location (or use GPS)
        ↓
Device saves config to EEPROM/Flash
        ↓
Device reboots and connects to home WiFi
        ↓
Device sends registration message via MQTT
        ↓
Device enters SLEEP mode
```

#### **Phase 2: Normal Days (99% of the time)**

```
Device is in DEEP SLEEP mode
        ↓
Power consumption: ~0.5mA
        ↓
Battery life: ~2 years on 3000mAh
        ↓
Device does NOTHING - just sleeps
```

#### **Phase 3: Collection Day (Wake on Command)**

```
8:00 AM - Backend sends "wake_up" command via MQTT
        ↓
Device wakes from deep sleep
        ↓
Every 1 hour for 12 hours:
    │
    ├── Read weight sensor → Calculate fill %
    ├── Read battery voltage
    ├── Read temperature sensor
    ├── Get GPS coordinates (optional)
    │
    └── Publish telemetry via MQTT
        ↓
8:00 PM - Backend sends "sleep" command
        ↓
Device returns to deep sleep
```

---

### MQTT Topics for Hardware

#### **Topics to SUBSCRIBE (Listen for commands):**

```
cleanroute/bins/{BIN_ID}/command      # Commands for this specific bin
cleanroute/bins/broadcast/command     # Commands for ALL bins
```

#### **Topics to PUBLISH (Send data):**

```
cleanroute/bins/{BIN_ID}/telemetry    # Regular sensor readings
cleanroute/bins/{BIN_ID}/register     # First-time registration
cleanroute/bins/{BIN_ID}/ack          # Command acknowledgment
```

---

### Message Formats for Hardware

#### **1. Telemetry Message (Device → Backend)**

Publish to: `cleanroute/bins/B001/telemetry`

```json
{
  "bin_id": "B001",
  "ts": "2025-12-12T10:00:00Z",
  "fill_pct": 72.5,
  "batt_v": 3.85,
  "temp_c": 31.4,
  "emptied": 0,
  "lat": 6.9102,
  "lon": 79.8623
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bin_id` | string | Yes | Unique bin identifier |
| `ts` | ISO8601 | Yes | Timestamp in UTC |
| `fill_pct` | float | Yes | Fill percentage (0-100) |
| `batt_v` | float | ⬜ | Battery voltage |
| `temp_c` | float | ⬜ | Temperature in Celsius |
| `emptied` | int | ⬜ | 1 if just emptied, 0 otherwise |
| `lat` | float | ⬜ | GPS latitude |
| `lon` | float | ⬜ | GPS longitude |

#### **2. Registration Message (Device → Backend)**

Publish to: `cleanroute/bins/B001/register`

```json
{
  "bin_id": "B001",
  "user_id": "USER001",
  "user_name": "John Doe",
  "user_phone": "+94771234567",
  "wifi_ssid": "HomeWiFi",
  "firmware_version": "1.0.0",
  "lat": 6.9102,
  "lon": 79.8623
}
```

#### **3. Wake Up Command (Backend → Device)**

Subscribe to: `cleanroute/bins/B001/command`

```json
{
  "command": "wake_up",
  "timestamp": "2025-12-12T08:00:00Z",
  "params": {
    "collection_hours": 12,
    "telemetry_interval_minutes": 60
  }
}
```

**Action:** Exit deep sleep, start sending telemetry every 60 minutes for 12 hours.

#### **4. Sleep Command (Backend → Device)**

```json
{
  "command": "sleep",
  "timestamp": "2025-12-12T20:00:00Z",
  "params": {}
}
```

**Action:** Enter deep sleep mode immediately.

#### **5. Other Commands**

| Command | Description |
|---------|-------------|
| `reset_emptied` | Reset the emptied flag |
| `get_status` | Request immediate telemetry |
| `update_config` | Update device settings |

---

### Hardware Checklist

- [ ] ESP32 with WiFi capability
- [ ] AP mode for WiFi setup (captive portal)
- [ ] MQTT client library (PubSubClient or similar)
- [ ] Deep sleep implementation
- [ ] Wake on MQTT message OR timer
- [ ] Weight sensor (HX711 + load cell)
- [ ] Battery voltage reading (ADC)
- [ ] Temperature sensor (optional)
- [ ] GPS module (optional)
- [ ] LED indicators for status
- [ ] Waterproof enclosure

---

## For UI/ML Team (Person 3)

### What the Backend Provides

The backend exposes a REST API at `http://localhost:8000` with these endpoints:

---

### API Endpoints for UI

#### **1. Get All Bins with Latest Status**

```bash
GET /bins/latest
```

**Response:**
```json
[
  {
    "bin_id": "B001",
    "lat": 6.9102,
    "lon": 79.8623,
    "fill_pct": 72.5,
    "batt_v": 3.85,
    "temp_c": 31.4,
    "last_seen": "2025-12-12T10:00:00Z",
    "last_emptied": null,
    "last_telemetry_ts": "2025-12-12T10:00:00Z"
  }
]
```

**Use for:** Map view, bin list, real-time dashboard

---

#### **2. Get Historical Data (For ML/Charts)**

```bash
GET /telemetry/recent?bin_id=B001&limit=1000
```

**Response:**
```json
[
  {
    "id": 123,
    "ts": "2025-12-12T10:00:00Z",
    "bin_id": "B001",
    "fill_pct": 72.5,
    "batt_v": 3.85,
    "temp_c": 31.4,
    "emptied": false,
    "received_at": "2025-12-12T10:00:05Z"
  }
]
```

**Use for:** ML training, trend charts, pattern analysis

---

#### **3. Fleet Health Overview**

```bash
GET /fleet/health
```

**Response:**
```json
{
  "total_bins": 50,
  "online_bins": 45,
  "offline_bins": 5,
  "sleeping_bins": 40,
  "active_bins": 10,
  "alert_summary": {
    "battery_low": {"critical": 2, "warning": 5},
    "overflow_risk": {"critical": 3, "warning": 8},
    "device_offline": {"warning": 5}
  }
}
```

**Use for:** Dashboard KPIs, status summary

---

#### **4. Device Health (Single Bin)**

```bash
GET /devices/B001/health
```

**Response:**
```json
{
  "bin_id": "B001",
  "online": true,
  "sleep_mode": false,
  "battery": {
    "voltage": 3.85,
    "status": "ok"
  },
  "fill": {
    "percentage": 72.5,
    "status": "warning"
  },
  "last_seen": "2025-12-12T10:00:00Z",
  "minutes_since_seen": 15,
  "user": {
    "id": "USER001",
    "name": "John Doe",
    "phone": "+94771234567"
  },
  "unresolved_alerts": 0
}
```

**Use for:** Device detail view, troubleshooting

---

#### **5. Get Alerts**

```bash
GET /alerts
GET /alerts?bin_id=B001
```

**Response:**
```json
{
  "alerts": [
    {
      "id": 1,
      "bin_id": "B001",
      "alert_type": "battery_low",
      "severity": "critical",
      "message": "Low battery: 3.2V (bin B001)",
      "created_at": "2025-12-12T10:00:00Z"
    }
  ]
}
```

**Alert Types:**
- `battery_low` - Battery < 3.5V
- `device_offline` - No data > 60 minutes
- `overflow_risk` - Fill > 90%
- `collection_reminder` - User notification

---

#### **6. System Health**

```bash
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "database": true,
  "mqtt": {
    "connected": true,
    "broker": "localhost:1883",
    "topic": "cleanroute/bins/+/telemetry",
    "messages_processed": 150
  },
  "timestamp": "2025-12-12T10:00:00Z"
}
```

---

### Command API (For Dashboard Controls)

#### **Start Collection Day**

```bash
POST /collection/start?collection_hours=12
```

**What it does:**
- Sends wake_up command to ALL bins via MQTT
- Creates reminder alerts for all users
- Returns count of bins notified

---

#### **End Collection Day**

```bash
POST /collection/end
```

**What it does:**
- Sends sleep command to ALL bins
- Devices enter low-power mode

---

#### **Send Reminders**

```bash
POST /collection/remind
```

**What it does:**
- Creates alerts for bins that are still offline
- For future: trigger SMS/push notifications

---

#### **Wake Single Bin**

```bash
POST /commands/B001/wake?collection_hours=12
```

---

#### **Sleep Single Bin**

```bash
POST /commands/B001/sleep
```

---

#### **Resolve Alert**

```bash
POST /alerts/123/resolve
```

---

### Dashboard Features to Build

#### **1. Map View**
- Show all bins as markers
- Color code by fill level:
  - 🟢 Green: < 80%
  - 🟡 Yellow: 80-90%
  - 🔴 Red: > 90%
- Show online/offline status (grayed out = offline)
- Click marker → show details popup

#### **2. Control Panel**
- "Start Collection Day" button
- "End Collection Day" button
- "Send Reminders" button
- Filter by status (online/offline/all)

#### **3. Alerts Panel**
- List of unresolved alerts
- Badge with count
- Critical alerts in red
- "Resolve" button for each

#### **4. Fleet Statistics**
- Total bins
- Online vs offline
- Average fill level
- Bins at risk (>90%)

#### **5. Analytics (ML Features)**
- Fill level trends (line chart)
- Prediction: "Time to full" for each bin
- Heatmap of high-activity areas
- Collection route suggestions

---

### Real-Time Updates

**Option 1: Polling (Simple)**
```javascript
// Poll every 30 seconds
setInterval(async () => {
  const response = await fetch('/bins/latest');
  const bins = await response.json();
  updateMap(bins);
}, 30000);
```

**Option 2: WebSockets (Future)**
- Backend can be extended to push updates
- More efficient for real-time

---

### UI Checklist

- [ ] Map component (Leaflet.js, Google Maps, or Mapbox)
- [ ] REST API integration
- [ ] Real-time polling (30 sec interval)
- [ ] Alerts notification panel
- [ ] Collection day control buttons
- [ ] Device detail view
- [ ] Charts for analytics (Chart.js, Recharts)
- [ ] Responsive design for mobile

---

## Complete Collection Day Flow

### Timeline Example

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COLLECTION DAY TIMELINE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  8:00 AM - MORNING START                                                    │
│  ─────────────────────────────────────────────────────────                  │
│  1. Municipal operator opens dashboard                                      │
│  2. Clicks "Start Collection Day"                                           │
│  3. Backend broadcasts wake_up command via MQTT                             │
│  4. All devices wake from sleep                                             │
│  5. Reminder alerts created for users                                       │
│                                                                             │
│  9:00 AM - FIRST TELEMETRY                                                  │
│  ─────────────────────────────────────────────────────────                  │
│  1. Devices read sensors                                                    │
│  2. Publish telemetry to MQTT                                               │
│  3. Backend receives and stores data                                        │
│  4. Dashboard updates with new data                                         │
│  5. Map shows current fill levels                                           │
│                                                                             │
│  10:00 AM - HEALTH CHECK                                                    │
│  ─────────────────────────────────────────────────────────                  │
│  1. Backend detects 3 devices didn't respond                                │
│  2. Creates "device_offline" alerts                                         │
│  3. Dashboard shows offline bins in gray                                    │
│  4. Operator clicks "Send Reminders"                                        │
│  5. Users notified to check their devices                                   │
│                                                                             │
│  10:00 AM - 8:00 PM - HOURLY UPDATES                                        │
│  ─────────────────────────────────────────────────────────                  │
│  • Every hour: devices send new readings                                    │
│  • Dashboard auto-refreshes every 30 seconds                                │
│  • Overflow alerts created for bins > 90%                                   │
│  • ML predicts which bins will overflow next                                │
│                                                                             │
│  8:00 PM - EVENING END                                                      │
│  ─────────────────────────────────────────────────────────                  │
│  1. Operator clicks "End Collection Day"                                    │
│  2. Backend broadcasts sleep command                                        │
│  3. All devices enter deep sleep                                            │
│  4. Dashboard shows collection complete                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   DEVICE    │         │   BACKEND   │         │     UI      │
│  (ESP32)    │         │  (FastAPI)  │         │   (React)   │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                       │
       │  1. Telemetry (MQTT)  │                       │
       │──────────────────────>│                       │
       │                       │                       │
       │                       │  2. Store in DB       │
       │                       │──────────────>        │
       │                       │                       │
       │                       │  3. Poll API          │
       │                       │<──────────────────────│
       │                       │                       │
       │                       │  4. Return JSON       │
       │                       │──────────────────────>│
       │                       │                       │
       │                       │  5. User clicks       │
       │                       │     "Wake Bin"        │
       │                       │<──────────────────────│
       │                       │                       │
       │  6. Command (MQTT)    │                       │
       │<──────────────────────│                       │
       │                       │                       │
       │  7. ACK (optional)    │                       │
       │──────────────────────>│                       │
       │                       │                       │
```

---

## Team Responsibilities Summary

### Hardware (Person 1)
| Task | Status |
|------|--------|
| ESP32 firmware | ⏳ |
| AP mode WiFi setup | ⏳ |
| MQTT client | ⏳ |
| Deep sleep / wake | ⏳ |
| Weight sensor | ⏳ |
| Battery reading | ⏳ |
| Enclosure design | ⏳ |

### Backend (Person 2)
| Task | Status |
|------|--------|
| MQTT subscriber | Yes |
| MQTT publisher (commands) | Yes |
| PostgreSQL storage | Yes |
| REST API (25 endpoints) | Yes |
| Health monitoring | Yes |
| Alerts system | Yes |
| Collection workflow | Yes |

### UI/ML (Person 3)
| Task | Status |
|------|--------|
| Map view | ⏳ |
| Real-time updates | ⏳ |
| Control buttons | ⏳ |
| Alerts panel | ⏳ |
| Analytics charts | ⏳ |
| ML predictions | ⏳ |
| Mobile responsive | ⏳ |

---

## Testing Together

### Test Flow 1: Device → Backend → UI

```bash
# Terminal 1: Start backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Simulate device sending telemetry
mosquitto_pub -h localhost -t cleanroute/bins/B001/telemetry -m '{
  "bin_id":"B001",
  "ts":"2025-12-12T10:00:00Z",
  "fill_pct":72.5,
  "batt_v":3.85,
  "temp_c":31.4,
  "lat":6.9102,
  "lon":79.8623
}'

# Terminal 3: Check API (what UI would call)
curl http://localhost:8000/bins/latest | jq
```

### Test Flow 2: UI → Backend → Device

```bash
# Terminal 1: Monitor what device receives
mosquitto_sub -h localhost -t 'cleanroute/bins/+/command' -v

# Terminal 2: Simulate UI sending command
curl -X POST http://localhost:8000/commands/B001/wake

# You should see the command in Terminal 1!
```

---

## 📚 Quick Links

- **Backend API Docs**: http://localhost:8000/docs
- **QUICKSTART.md**: How to run the backend
- **ARCHITECTURE.md**: System design diagrams
- **DEVICE_SETUP.md**: Hardware WiFi setup options
- **IMPLEMENTATION_SUMMARY.md**: What's been built

---

## ❓ FAQ

### For Hardware:
**Q: What if device can't connect to MQTT?**
A: Store readings locally, send when reconnected.

**Q: How does device know when to wake up?**
A: MQTT broker delivers message when device reconnects, OR use timer-based wake.

**Q: What's the minimum payload?**
A: `bin_id`, `ts`, `fill_pct` are required. Others optional.

### For UI:
**Q: How often should I poll the API?**
A: Every 30 seconds is good. Don't go below 10 seconds.

**Q: How do I know if a device is offline?**
A: Check `last_seen` timestamp. If > 60 minutes ago, it's offline.

**Q: Where do I get bin locations?**
A: `lat` and `lon` fields in `/bins/latest` response.

---

## Next Steps

1. **Hardware**: Implement MQTT on ESP32, test with backend
2. **UI**: Build basic map view, connect to API
3. **Integration**: Test full flow together
4. **Deploy**: Move to cloud (Oracle Free Tier)

---

**Questions? Check the documentation files or ask the backend person (Person 2)!**
