#!/bin/bash

# CleanRoute Stop Script
# Stops all running CleanRoute services

echo "🛑 Stopping CleanRoute Services..."
echo "════════════════════════════════════════════════════════════════"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop Frontend (Flask on port 5001)
echo "Stopping Frontend..."
FRONTEND_PID=$(lsof -ti:5001)
if [ ! -z "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ Frontend stopped${NC}"
else
    echo "Frontend not running"
fi

# Stop Backend (FastAPI on port 8000)
echo "Stopping Backend API..."
BACKEND_PID=$(lsof -ti:8000)
if [ ! -z "$BACKEND_PID" ]; then
    kill $BACKEND_PID 2>/dev/null
    echo -e "${GREEN}✅ Backend API stopped${NC}"
else
    echo "Backend not running"
fi

# Stop MQTT Ingest
echo "Stopping MQTT Ingest..."
MQTT_INGEST_PID=$(pgrep -f "python -m app.mqtt_ingest")
if [ ! -z "$MQTT_INGEST_PID" ]; then
    kill $MQTT_INGEST_PID 2>/dev/null
    echo -e "${GREEN}✅ MQTT Ingest stopped${NC}"
else
    echo "MQTT Ingest not running"
fi

# Optional: Stop MQTT Broker
read -p "Stop MQTT broker (mosquitto)? (y/N): " stop_mqtt
if [[ $stop_mqtt =~ ^[Yy]$ ]]; then
    pkill mosquitto
    echo -e "${GREEN}✅ MQTT broker stopped${NC}"
fi

# Optional: Stop PostgreSQL Docker container
if docker ps --format '{{.Names}}' | grep -q '^cleanroute-postgres$'; then
    read -p "Stop PostgreSQL container? (y/N): " stop_postgres
    if [[ $stop_postgres =~ ^[Yy]$ ]]; then
        docker stop cleanroute-postgres > /dev/null 2>&1
        echo -e "${GREEN}✅ PostgreSQL stopped${NC}"
        echo "(Container preserved. Run 'docker rm cleanroute-postgres' to remove it)"
    else
        echo "PostgreSQL container left running"
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}🎉 All services stopped${NC}"
echo "════════════════════════════════════════════════════════════════"
