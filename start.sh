#!/bin/bash

# CleanRoute Startup Script for macOS/Linux
# This script starts the CleanRoute frontend dashboard

echo "🚀 Starting CleanRoute Dashboard..."
echo "=================================="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Check if virtual environment exists
if [ ! -d "$BACKEND_DIR/.venv" ]; then
    echo "❌ Error: Virtual environment not found at $BACKEND_DIR/.venv"
    echo "Please run setup.sh first"
    exit 1
fi

# Check if mock data exists
if [ ! -f "$BACKEND_DIR/mock_data/bins_config.csv" ]; then
    echo "❌ Error: Mock data not found"
    echo "Please generate mock data first by running:"
    echo "  cd backend && python generate_mock_data.py --csv-only"
    exit 1
fi

# Activate virtual environment and start frontend
cd "$BACKEND_DIR"
source .venv/bin/activate
cd "$FRONTEND_DIR"

echo ""
echo "✅ Starting Flask server..."
echo "📍 Dashboard URL: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="
echo ""

python app.py
