#!/bin/bash

# CleanRoute Setup Script
# This script sets up the Python environment and installs dependencies

echo "🔧 Setting up CleanRoute..."
echo "============================"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"

cd "$BACKEND_DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

echo "✅ Found Python: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing dependencies..."
pip install flask flask-cors pandas numpy python-dateutil requests psycopg2-binary paho-mqtt fastapi uvicorn

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the dashboard, run:"
echo "  ./start.sh"
echo ""
echo "Or manually:"
echo "  cd backend && source .venv/bin/activate && cd ../frontend && python app.py"
echo ""
