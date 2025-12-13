# CleanRoute AI - Smart Waste Bin Monitoring System

IoT-based waste bin monitoring and route optimization backend.

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for setup instructions.

```bash
# Terminal 1: MQTT Broker (Secure)
mosquitto -c mqtt/mosquitto_secure.conf -v

# Terminal 2: Backend API
cd backend && source .venv/bin/activate && source .env.secure && uvicorn app.main:app --port 8000

# Terminal 3: Frontend
cd frontend && source ../backend/.venv/bin/activate && python app.py
```

**Access:**
- Dashboard: http://localhost:5001
- API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
cleanroute-backend/
├── backend/           # FastAPI + PostgreSQL + MQTT
│   └── app/           # Python modules
├── frontend/          # Flask + Leaflet.js dashboard
├── mqtt/              # Mosquitto config, certs, credentials
│   ├── certs/         # TLS certificates
│   └── passwd         # Device credentials
└── docs/              # Documentation
    ├── ARCHITECTURE.md   # System design
    ├── TEAM_GUIDE.md     # Team collaboration guide
    └── DEVICE_SETUP.md   # Hardware setup
```

## Security

- **TLS encryption** on port 8883
- **Device authentication** via username/password
- See `mqtt/CREDENTIALS.md` for device credentials

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Get running in 5 minutes |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design & data flow |
| [docs/TEAM_GUIDE.md](docs/TEAM_GUIDE.md) | Team collaboration |
| [docs/DEVICE_SETUP.md](docs/DEVICE_SETUP.md) | ESP32/Hardware setup |

## Tech Stack

- **Backend:** FastAPI, PostgreSQL, Paho-MQTT
- **Frontend:** Flask, Leaflet.js
- **IoT:** Mosquitto MQTT (TLS + Auth)
- **ML:** EWMA prediction, Greedy routing
