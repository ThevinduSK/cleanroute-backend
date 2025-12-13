# 🚀 CleanRoute Startup Guide

## Quick Start

### Option 1: CSV Mode (Simplest - Recommended for Development)
```bash
./start.sh
# Select option 1 when prompted
```
Then visit: http://localhost:5001

### Option 2: Full System Mode (PostgreSQL + MQTT)
```bash
./start.sh
# Select option 2 when prompted
```

---

## 📋 Startup Script Options

The `start.sh` script now supports two modes:

### 🟢 CSV Mode (Simple)
- **No database required**
- Uses mock CSV data files
- Perfect for development & testing
- Starts only the Flask frontend

### 🔵 Full System Mode (Production-Ready)
- **PostgreSQL database integration**
- **MQTT broker for real-time IoT data**
- **FastAPI backend REST API**
- **MQTT ingest service** (optional)
- Full production architecture

---

## 🛠️ Prerequisites

### For CSV Mode:
- Python 3.9+
- Virtual environment (created by `setup.sh`)

### For Full System Mode:
**Additional requirements:**
- PostgreSQL 15+ (Docker or native)
- Mosquitto MQTT broker (optional)
- All Python dependencies (installed by `setup.sh`)

---

## 📦 First-Time Setup

```bash
# 1. Run setup script (installs all dependencies)
./setup.sh

# 2. Generate mock data (if not already done)
cd backend
source .venv/bin/activate
python generate_mock_data.py
cd ..

# 3. Start the system
./start.sh
```

---

## 🔧 Full System Setup

### Step 1: Start PostgreSQL

**Option A: Docker (Recommended)**
```bash
docker run --name cleanroute-postgres \
  -e POSTGRES_DB=cleanroute_db \
  -e POSTGRES_USER=cleanroute_user \
  -e POSTGRES_PASSWORD=cleanroute_pass \
  -p 5432:5432 -d postgres:15
```

**Option B: Native Installation**
```bash
brew install postgresql@15
brew services start postgresql@15
createdb cleanroute_db
```

### Step 2: Create Database Schema
```bash
cd backend
source .venv/bin/activate
# TODO: Run schema creation script when available
# psql -U cleanroute_user -d cleanroute_db -f schema.sql
```

### Step 3: Start MQTT Broker (Optional)
```bash
# Install Mosquitto
brew install mosquitto

# Start with secure config
cd mqtt
mosquitto -c mosquitto_secure.conf
```

### Step 4: Start the System
```bash
./start.sh
# Select option 2 (Full System)
```

---

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend Dashboard** | http://localhost:5001 | Main map interface |
| **Districts View** | http://localhost:5001/districts | Grouped by district |
| **Backend API** | http://localhost:8000 | REST API endpoints |
| **API Documentation** | http://localhost:8000/docs | Swagger UI |
| **MQTT Broker** | mqtt://localhost:1883 | Insecure (dev) |
| **MQTT Secure** | mqtts://localhost:8883 | TLS encrypted |

---

## 🛑 Stopping Services

### Quick Stop
```bash
./stop.sh
```

### Manual Stop
```bash
# Stop all Python services
pkill -f "python app.py"
pkill -f "uvicorn"
pkill -f "mqtt_ingest"

# Or kill specific ports
kill $(lsof -ti:5001)  # Frontend
kill $(lsof -ti:8000)  # Backend
```

---

## 📊 Environment Variables

### CSV Mode
```bash
export USE_BACKEND=false
```

### Full System Mode
```bash
export USE_BACKEND=true
export BACKEND_URL=http://localhost:8000

# PostgreSQL
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=cleanroute_db
export POSTGRES_USER=cleanroute_user
export POSTGRES_PASSWORD=cleanroute_pass

# MQTT (optional)
export MQTT_BROKER=localhost
export MQTT_PORT=1883
export MQTT_USE_TLS=false  # Set to true for port 8883
```

---

## 🔍 Troubleshooting

### Frontend won't start
```bash
# Check if port 5001 is in use
lsof -i:5001

# Check logs
tail -f frontend.log
```

### Backend API errors
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Check logs
tail -f backend.log
```

### Database connection failed
```bash
# Test PostgreSQL connection
psql -h localhost -U cleanroute_user -d cleanroute_db

# Check if database exists
psql -U postgres -c "\\l" | grep cleanroute
```

### MQTT not working
```bash
# Check if Mosquitto is running
ps aux | grep mosquitto

# Test MQTT connection
mosquitto_pub -h localhost -t test -m "hello"
```

---

## 📝 Log Files

When running in Full System mode, logs are created:
- `backend.log` - FastAPI backend logs
- `frontend.log` - Flask frontend logs  
- `mqtt_ingest.log` - MQTT ingest service logs

View in real-time:
```bash
tail -f backend.log frontend.log mqtt_ingest.log
```

---

## 🎯 Development Workflow

### Daily Development (CSV Mode)
```bash
./start.sh  # Select option 1
# Make changes
# Refresh browser
```

### Testing Full Stack
```bash
# Start all services
./start.sh  # Select option 2

# Test API
curl http://localhost:8000/bins/latest

# Test frontend
open http://localhost:5001

# Stop when done
./stop.sh
```

---

## 🚀 What Each Component Does

### Frontend (Flask - Port 5001)
- Web dashboard with interactive map
- ML prediction visualization
- Route optimization display
- Can work with backend API OR CSV files

### Backend (FastAPI - Port 8000)
- REST API for bins, telemetry, alerts
- Integrates with PostgreSQL
- Provides data to frontend

### MQTT Ingest (Background Service)
- Listens to MQTT topics
- Receives real-time IoT sensor data
- Stores in PostgreSQL database

### MQTT Broker (Mosquitto - Ports 1883/8883)
- Receives data from IoT devices
- Routes messages to subscribers
- Supports TLS encryption (port 8883)

---

## 💡 Tips

1. **Use CSV mode** for quick development - no database needed
2. **Use Full System mode** when testing IoT integration
3. Check log files if something doesn't work
4. The frontend automatically falls back to CSV if backend is unavailable
5. You can switch modes without restarting by changing `USE_BACKEND` env var

---

## 📞 Need Help?

Check these in order:
1. Log files (`*.log` in project root)
2. Error messages in terminal
3. Browser console (F12) for frontend issues
4. API documentation at http://localhost:8000/docs

---

**Happy coding! 🎉**
