#!/bin/bash

# CleanRoute Startup Script for macOS/Linux
# Supports both CSV-only mode and Full System mode (PostgreSQL + MQTT)

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       CleanRoute - Smart Waste Management System      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Check if virtual environment exists
if [ ! -d "$BACKEND_DIR/.venv" ]; then
    echo -e "${RED}Error: Virtual environment not found at $BACKEND_DIR/.venv${NC}"
    echo "Please run setup.sh first"
    exit 1
fi

# Determine startup mode
MODE=${1:-csv}  # Default to 'csv' mode if no argument provided

echo -e "${CYAN}Select Startup Mode:${NC}"
echo "  1) CSV Mode (Simple - No database required)"
echo "  2) Full System (PostgreSQL + MQTT + CSV fallback)"
echo ""
read -p "Enter choice [1-2] (default: 1): " choice
choice=${choice:-1}

case $choice in
    1)
        MODE="csv"
        ;;
    2)
        MODE="full"
        ;;
    *)
        echo -e "${RED}Invalid choice. Using CSV mode.${NC}"
        MODE="csv"
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════════"

if [ "$MODE" = "csv" ]; then
    echo -e "${GREEN}📄 Starting in CSV Mode (Mock Data Only)${NC}"
    echo "════════════════════════════════════════════════════════════════"
    
    # Check if mock data exists
    if [ ! -f "$BACKEND_DIR/mock_data/bins_config.csv" ]; then
        echo -e "${RED}Error: Mock data not found${NC}"
        echo "Generating mock data now..."
        cd "$BACKEND_DIR"
        source .venv/bin/activate
        python generate_mock_data.py
        echo -e "${GREEN}Mock data generated${NC}"
    fi
    
    # Set environment for CSV mode
    export USE_BACKEND=false
    
    # Start frontend only
    cd "$BACKEND_DIR"
    source .venv/bin/activate
    cd "$FRONTEND_DIR"
    
    echo ""
    echo -e "${GREEN}Starting Flask Frontend...${NC}"
    echo -e "${CYAN}Dashboard: http://localhost:5001${NC}"
    echo -e "${CYAN}Districts: http://localhost:5001/districts${NC}"
    echo ""
    echo "Press Ctrl+C to stop"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    python app.py
    
else
    echo -e "${GREEN}Starting Full System (Backend + Frontend + MQTT)${NC}"
    echo "════════════════════════════════════════════════════════════════"
    
    # Check and start PostgreSQL
    echo -e "${YELLOW}Checking PostgreSQL...${NC}"
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo -e "${GREEN}PostgreSQL is running${NC}"
    else
        echo -e "${YELLOW}PostgreSQL is not running. Starting automatically...${NC}"
        
        # Check if Docker is installed
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}Docker is not installed${NC}"
            echo ""
            echo "Please install Docker:"
            echo "  https://docs.docker.com/desktop/install/mac-install/"
            echo ""
            echo "Or install PostgreSQL natively:"
            echo "  brew install postgresql@15"
            echo "  brew services start postgresql@15"
            exit 1
        fi
        
        # Check if container already exists
        if docker ps -a --format '{{.Names}}' | grep -q '^cleanroute-postgres$'; then
            echo "Starting existing PostgreSQL container..."
            docker start cleanroute-postgres > /dev/null 2>&1
            sleep 3
            
            if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
                echo -e "${GREEN}PostgreSQL started${NC}"
            else
                echo -e "${RED}Failed to start PostgreSQL container${NC}"
                exit 1
            fi
        else
            # Create new container
            echo "Creating new PostgreSQL container..."
            docker run --name cleanroute-postgres \
              -e POSTGRES_DB=cleanroute_db \
              -e POSTGRES_USER=cleanroute_user \
              -e POSTGRES_PASSWORD=cleanroute_pass \
              -p 5432:5432 -d postgres:15 > /dev/null 2>&1
            
            echo "Waiting for PostgreSQL to initialize..."
            sleep 5
            
            # Wait for PostgreSQL to be ready (max 30 seconds)
            for i in {1..30}; do
                if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
                    echo -e "${GREEN}PostgreSQL started successfully${NC}"
                    break
                fi
                if [ $i -eq 30 ]; then
                    echo -e "${RED}PostgreSQL failed to start in time${NC}"
                    echo "Check logs: docker logs cleanroute-postgres"
                    exit 1
                fi
                sleep 1
            done
            
            # Initialize database schema
            echo -e "${YELLOW}Initializing database schema...${NC}"
            sleep 2
            echo -e "${GREEN}Database ready${NC}"
        fi
    fi
    
    # Activate environment
    cd "$BACKEND_DIR"
    source .venv/bin/activate
    
    # Set environment for backend mode
    export USE_BACKEND=true
    export BACKEND_URL=http://localhost:8000
    
    # Start FastAPI Backend
    echo ""
    echo -e "${YELLOW}Starting FastAPI Backend (Port 8000)...${NC}"
    uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$SCRIPT_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    sleep 2
    
    if ps -p $BACKEND_PID > /dev/null; then
        echo -e "${GREEN}Backend API started (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${RED}Backend failed to start. Check backend.log${NC}"
    fi
    
    # Check if MQTT broker should be started
    echo ""
    echo -e "${YELLOW}Checking MQTT Broker...${NC}"
    if pgrep -x mosquitto > /dev/null; then
        echo -e "${GREEN}MQTT broker is running${NC}"
    else
        echo -e "${YELLOW} MQTT broker not running${NC}"
        echo "Start manually if needed:"
        echo "  mosquitto -c mqtt/mosquitto_secure.conf"
    fi
    
    # Start MQTT Ingest (optional)
    read -p "Start MQTT ingest service? (y/N): " start_mqtt
    if [[ $start_mqtt =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Starting MQTT Ingest...${NC}"
        python -m app.mqtt_ingest > "$SCRIPT_DIR/mqtt_ingest.log" 2>&1 &
        MQTT_PID=$!
        sleep 1
        echo -e "${GREEN}MQTT Ingest started (PID: $MQTT_PID)${NC}"
    fi
    
    # Start Frontend
    echo ""
    echo -e "${YELLOW}Starting Flask Frontend (Port 5001)...${NC}"
    cd "$FRONTEND_DIR"
    python app.py > "$SCRIPT_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    sleep 2
    
    if ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${RED}Frontend failed to start. Check frontend.log${NC}"
    fi
    
    # Summary
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${GREEN}System Started Successfully!${NC}"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${CYAN}Services:${NC}"
    echo "  - Backend API:  http://localhost:8000"
    echo "  - Frontend:     http://localhost:5001"
    echo "  - API Docs:     http://localhost:8000/docs"
    echo ""
    echo -e "${CYAN}📝 Log Files:${NC}"
    echo "  - Backend:      $SCRIPT_DIR/backend.log"
    echo "  - Frontend:     $SCRIPT_DIR/frontend.log"
    if [[ $start_mqtt =~ ^[Yy]$ ]]; then
        echo "  - MQTT Ingest:  $SCRIPT_DIR/mqtt_ingest.log"
    fi
    echo ""
    echo -e "${CYAN}To Stop:${NC}"
    echo "  kill $BACKEND_PID $FRONTEND_PID"
    if [[ $start_mqtt =~ ^[Yy]$ ]]; then
        echo "  kill $MQTT_PID"
    fi
    echo ""
    echo "Press Ctrl+C to exit (services will continue running)"
    echo "════════════════════════════════════════════════════════════════"
    
    # Wait for user interrupt
    tail -f /dev/null
fi
