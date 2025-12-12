# CleanRoute Backend

Backend service for the CleanRoute AI smart waste bin monitoring system.

## Features

- **MQTT Ingest**: Subscribes to `cleanroute/bins/+/telemetry` for real-time bin data
- **PostgreSQL Storage**: Persists bin metadata and telemetry time-series
- **FastAPI REST API**: Exposes endpoints for the Planner UI

## Quick Start

### 1. Prerequisites

```bash
# Mosquitto MQTT Broker
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto

# PostgreSQL
sudo systemctl status postgresql
```

### 2. Create Database

```bash
sudo -u postgres psql -c "CREATE USER cleanroute_user WITH PASSWORD 'cleanroute_pass';"
sudo -u postgres psql -c "CREATE DATABASE cleanroute_db OWNER cleanroute_user;"
```

### 3. Create Tables

```bash
psql "dbname=cleanroute_db user=cleanroute_user password=cleanroute_pass host=localhost" -c "
CREATE TABLE IF NOT EXISTS bins (
  bin_id TEXT PRIMARY KEY,
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION,
  last_seen TIMESTAMPTZ,
  last_emptied TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS telemetry (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL,
  bin_id TEXT NOT NULL REFERENCES bins(bin_id),
  fill_pct DOUBLE PRECISION NOT NULL CHECK (fill_pct >= 0 AND fill_pct <= 100),
  batt_v DOUBLE PRECISION,
  temp_c DOUBLE PRECISION,
  emptied BOOLEAN DEFAULT FALSE,
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION,
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telemetry_bin_ts ON telemetry(bin_id, ts DESC);
"
```

### 4. Setup Python Environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | API info |
| `GET /health` | Health check (DB + MQTT status) |
| `GET /bins/latest` | Latest state of all bins |
| `GET /telemetry/recent?bin_id=B001&limit=100` | Recent telemetry for a bin |
| `GET /bins/at_risk` | Bins at overflow risk (coming soon) |

## Testing with MQTT

```bash
# Subscribe to see messages
mosquitto_sub -h localhost -t "cleanroute/#" -v

# Publish a test message
mosquitto_pub -h localhost -t cleanroute/bins/B001/telemetry -m '{
  "bin_id":"B001",
  "ts":"2025-12-12T10:00:00Z",
  "fill_pct":72.5,
  "batt_v":3.85,
  "temp_c":31.4,
  "emptied":0,
  "lat":6.9102,
  "lon":79.8623
}'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_BROKER` | localhost | MQTT broker hostname |
| `MQTT_PORT` | 1883 | MQTT broker port |
| `POSTGRES_HOST` | localhost | PostgreSQL hostname |
| `POSTGRES_PORT` | 5432 | PostgreSQL port |
| `POSTGRES_DB` | cleanroute_db | Database name |
| `POSTGRES_USER` | cleanroute_user | Database user |
| `POSTGRES_PASSWORD` | cleanroute_pass | Database password |

## Telemetry Payload Format

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

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py       # Configuration settings
│   ├── db.py           # Database connection & queries
│   ├── mqtt_ingest.py  # MQTT subscriber service
│   ├── api.py          # FastAPI routes
│   └── main.py         # Application entry point
├── requirements.txt
└── README.md
```
