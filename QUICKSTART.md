# CleanRoute - Quick Start Guide

## Prerequisites

- PostgreSQL running with database `cleanroute_db`
- Python 3.10+ with venv
- Mosquitto MQTT broker installed

---

## Start the Full Stack (4 Terminals)

### Terminal 1: MQTT Broker (Secure Mode)

```bash
# Stop system mosquitto if running
sudo systemctl stop mosquitto

# Start with TLS + Authentication
mosquitto -c /home/thevinduk/Repositories/cleanroute-backend/mqtt/mosquitto_secure.conf -v
```

**Expected output:**
```
mosquitto version 2.0.x starting
Opening ipv4 listen socket on port 1883 (localhost only)
Opening ipv4 listen socket on port 8883 (TLS)
```

---

### Terminal 2: FastAPI Backend (Secure Mode)

```bash
cd /home/thevinduk/Repositories/cleanroute-backend/backend && \
source .venv/bin/activate && \
source .env.secure && \
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Expected output:**
```
Starting CleanRoute Backend...
TLS enabled with CA: .../mqtt/certs/ca.crt
Authenticating as: backend_service
Connected to MQTT broker at localhost:8883
Subscribed to: cleanroute/bins/+/telemetry (QoS=1)
Uvicorn running on http://0.0.0.0:8000
```

---

### Terminal 3: Flask Frontend

```bash
cd /home/thevinduk/Repositories/cleanroute-backend/frontend && \
source ../backend/.venv/bin/activate && \
python app.py
```

**Expected output:**
```
Starting CleanRoute Frontend...
�� Dashboard: http://localhost:5001
🔗 Backend: http://localhost:8000 (enabled)
Running on http://0.0.0.0:5001
```

---

### Terminal 4: Load Demo Data (Colombo - 32 Bins)

#### Quick Demo (Recommended):
```bash
cd /home/thevinduk/Repositories/cleanroute-backend && \
./demo_colombo.sh
```

This publishes 32 bins across 4 Colombo zones:
- **Zone 1 (Fort & Pettah):** COL101-COL108
- **Zone 2 (Kollupitiya):** COL201-COL208  
- **Zone 3 (Wellawatta/Dehiwala):** COL301-COL308
- **Zone 4 (Nugegoda/Kotte):** COL401-COL408

#### Manual: Publish single bin:
```bash
mosquitto_pub -h localhost -p 8883 \
  --cafile /home/thevinduk/Repositories/cleanroute-backend/mqtt/certs/ca.crt \
  -u "COL101" -P "col_zone1_101" \
  -t "cleanroute/bins/COL101/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL101","fill_pct":85.0,"batt_v":3.8,"temp_c":31.0,"lat":6.9350,"lon":79.8450}'
```

---

## Access URLs

| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:5001 |
| Districts View | http://localhost:5001/districts |
| Backend API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## 📅 Collection Day Workflow

The system supports a zone-based collection workflow to manage device power efficiently.

### How It Works

1. **Devices Start Inactive**: Bins are in sleep mode to save battery (shown as grey 💤)
2. **Admin Starts Collection**: Admin logs in and wakes up devices in a zone
3. **Devices Report Status**: Bins wake up and send current fill levels
4. **Collection Happens**: Trucks collect waste from bins
5. **Admin Finishes**: Check which bins were collected (verify none missed)
6. **Admin Ends Collection**: Put all devices back to sleep

### Demo Simulation (Zone 4: Nugegoda & Kotte)

**Step 1: Initialize bins as sleeping**
```bash
./demo_zone4_init.sh
```

**Step 2: In the UI**
1. Open http://localhost:5001
2. Login as admin (panel on left sidebar)
3. Select **Colombo** → **Nugegoda & Kotte**
4. Bins should appear grey with 💤 (sleeping)
5. Click **"1. Start Collection (Wake Up)"**

**Step 3: Simulate devices responding**
```bash
./demo_zone4_wake.sh
```

**Step 4: In the UI**
1. Click **"2. Check Status"** - see bins responding
2. Bins turn green/orange/red showing fill levels
3. Click **"Optimize Zone Route"** to plan collection

**Step 5: Simulate collection complete**
```bash
./demo_zone4_collected.sh
```

**Step 6: Finish collection**
1. Click **"3. Finish (Verify)"** - all bins show low fill (green)
2. Click **"4. End Collection (Sleep)"** - devices go back to sleep
3. Bins turn grey with 💤 again

### First Time Setup (Create Admin User)

```bash
curl -X POST "http://localhost:8000/api/admin/setup?password=YourSecurePassword123"
```

---

## Device Credentials

### Backend Service
| Service | Username | Password |
|---------|----------|----------|
| Backend | `backend_service` | `CleanRoute@2025` |

### Colombo District - Demo Bins (32 total)

#### Zone 1: Fort & Pettah
| Bin ID | Username | Password |
|--------|----------|----------|
| COL101 | `COL101` | `col_zone1_101` |
| COL102 | `COL102` | `col_zone1_102` |
| COL103 | `COL103` | `col_zone1_103` |
| COL104 | `COL104` | `col_zone1_104` |
| COL105 | `COL105` | `col_zone1_105` |
| COL106 | `COL106` | `col_zone1_106` |
| COL107 | `COL107` | `col_zone1_107` |
| COL108 | `COL108` | `col_zone1_108` |

#### Zone 2: Kollupitiya & Bambalapitiya
| Bin ID | Username | Password |
|--------|----------|----------|
| COL201 | `COL201` | `col_zone2_201` |
| COL202 | `COL202` | `col_zone2_202` |
| COL203 | `COL203` | `col_zone2_203` |
| COL204 | `COL204` | `col_zone2_204` |
| COL205 | `COL205` | `col_zone2_205` |
| COL206 | `COL206` | `col_zone2_206` |
| COL207 | `COL207` | `col_zone2_207` |
| COL208 | `COL208` | `col_zone2_208` |

#### Zone 3: Wellawatta & Dehiwala
| Bin ID | Username | Password |
|--------|----------|----------|
| COL301 | `COL301` | `col_zone3_301` |
| COL302 | `COL302` | `col_zone3_302` |
| COL303 | `COL303` | `col_zone3_303` |
| COL304 | `COL304` | `col_zone3_304` |
| COL305 | `COL305` | `col_zone3_305` |
| COL306 | `COL306` | `col_zone3_306` |
| COL307 | `COL307` | `col_zone3_307` |
| COL308 | `COL308` | `col_zone3_308` |

#### Zone 4: Nugegoda & Kotte
| Bin ID | Username | Password |
|--------|----------|----------|
| COL401 | `COL401` | `col_zone4_401` |
| COL402 | `COL402` | `col_zone4_402` |
| COL403 | `COL403` | `col_zone4_403` |
| COL404 | `COL404` | `col_zone4_404` |
| COL405 | `COL405` | `col_zone4_405` |
| COL406 | `COL406` | `col_zone4_406` |
| COL407 | `COL407` | `col_zone4_407` |
| COL408 | `COL408` | `col_zone4_408` |

### Other Districts (Legacy)
| Bin ID | Username | Password |
|--------|----------|----------|
| GAL001 | `GAL001` | `galle_bin_001_secret` |
| KAN001 | `KAN001` | `kandy_bin_001_secret` |
| MAT001 | `MAT001` | `matara_bin_001_secret` |

### Add new device:
```bash
mosquitto_passwd -b mqtt/passwd <BIN_ID> <PASSWORD>
```

---

## Stopping Services

- **Terminal 1-3:** Press `Ctrl+C`
- **Kill by port:** `sudo kill $(sudo lsof -t -i:8000)`

---

## Troubleshooting

### "Address already in use"
```bash
# Kill process on port
sudo kill $(sudo lsof -t -i:8000)  # Backend
sudo kill $(sudo lsof -t -i:5001)  # Frontend
sudo systemctl stop mosquitto       # Broker
```

### Backend can't connect to MQTT
- Make sure Terminal 1 (Mosquitto) is running first
- Check TLS is enabled: `source .env.secure`

### Bins not showing on map
- Click "Fit All Bins" button
- Check bins have valid lat/lon coordinates
- View console (F12) for errors
