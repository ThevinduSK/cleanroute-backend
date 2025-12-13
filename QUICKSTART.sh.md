# CleanRoute Quick Start Guide

## 🚀 Starting the Dashboard

### Option 1: Using the start script (Recommended)

```bash
cd /Users/nbal0029/Desktop/IoT/cleanroute-backend
chmod +x start.sh
./start.sh
```

### Option 2: Manual start

```bash
cd /Users/nbal0029/Desktop/IoT/cleanroute-backend/backend
source .venv/bin/activate
cd ../frontend
python app.py
```

The dashboard will be available at: **http://localhost:5001**

## 🛠️ First Time Setup

If this is your first time running the project:

```bash
cd /Users/nbal0029/Desktop/IoT/cleanroute-backend
chmod +x setup.sh
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all required dependencies
- Prepare the system for running

## 📊 Using the Dashboard

1. **Open Browser**: Navigate to http://localhost:5001
2. **View Bins**: Map automatically loads with 30 bins across Colombo
3. **Generate Predictions**: 
   - Select date (defaults to tomorrow)
   - Select time (defaults to 2:00 PM)
   - Click "GENERATE PREDICTIONS"
4. **Optimize Route**:
   - After predictions, click "OPTIMIZE ROUTE"
   - Green route line appears with numbered waypoints
5. **View Details**: Click any bin marker to see 30-day history chart

## 🎨 Features

- ✅ 30 bins with real Colombo GPS coordinates
- ✅ ML predictions using EWMA algorithm
- ✅ Route optimization (greedy nearest-neighbor)
- ✅ Interactive map with Leaflet.js
- ✅ 30-day historical data visualization
- ✅ Real-time statistics
- ✅ Neo-tech/cyberpunk theme

## 🔧 Troubleshooting

### Server won't start
```bash
# Make sure virtual environment is activated
cd /Users/nbal0029/Desktop/IoT/cleanroute-backend/backend
source .venv/bin/activate

# Check if dependencies are installed
pip list | grep flask

# If not, install them
pip install flask flask-cors pandas numpy
```

### Port already in use
If port 5001 is busy, edit `frontend/app.py` line 377:
```python
app.run(host='0.0.0.0', port=5002, debug=True)  # Change 5001 to 5002
```

### No bins showing on map
- Check browser console (F12) for JavaScript errors
- Refresh the page (Cmd+R or Ctrl+R)
- Verify CSV files exist in `backend/mock_data/`

### Predictions/Routes not working
- Check terminal for Python errors
- Verify date/time format is valid
- Ensure CSV data has records for all bins

## 📁 Project Structure

```
cleanroute-backend/
├── start.sh              ← Run this to start dashboard
├── setup.sh              ← Run this for first-time setup
├── backend/
│   ├── .venv/           ← Python virtual environment
│   ├── app/             ← ML and routing modules
│   └── mock_data/       ← CSV data files
└── frontend/
    ├── app.py           ← Flask server
    ├── static/          ← CSS and JavaScript
    └── templates/       ← HTML files
```

## 🌐 URLs

- **Dashboard**: http://localhost:5001
- **API Stats**: http://localhost:5001/api/stats
- **API Bins**: http://localhost:5001/api/bins
- **API Predictions**: http://localhost:5001/api/predictions/2025-12-14-14-00
- **API Route**: http://localhost:5001/api/route/2025-12-14-14-00

## 🎯 Quick Commands

```bash
# Start dashboard
./start.sh

# Stop server
Press Ctrl+C in terminal

# View logs
Logs appear in terminal where you started the server

# Reset and restart
Ctrl+C to stop, then ./start.sh to restart
```

## 💡 Tips

1. **Keep terminal open** - The server runs in the terminal window
2. **Check for errors** - Terminal shows real-time logs and errors
3. **Refresh page** - If things look broken, try refreshing (Cmd+R)
4. **Use tomorrow's date** - Predictions work best for future dates
5. **Wait for predictions** - ML calculations take 1-2 seconds

## 🎉 You're Ready!

Your CleanRoute dashboard is configured and ready to use. Run `./start.sh` and start exploring your smart waste management system!
