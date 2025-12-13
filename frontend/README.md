# CleanRoute Frontend

Modern neo-tech themed web interface for smart waste management system with ML-powered predictions and route optimization.

## Features

### 🗺️ Interactive Map
- Real-time bin locations on Colombo map
- Color-coded markers (green: normal, orange: warning, red: critical)
- Click bins to see detailed information
- Responsive map controls

### 🤖 ML Predictions
- Predict bin fill levels at any future time
- EWMA-based forecasting algorithm
- Confidence indicators for predictions
- Visual feedback on map markers

### 🚛 Route Optimization
- Generate optimal collection routes
- Greedy nearest-neighbor algorithm
- Distance and time calculations
- Step-by-step waypoint display
- Visual route on map

### 📊 Real-time Statistics
- Total bins, active bins, warnings, critical alerts
- Average fill level across all bins
- Auto-refresh every 30 seconds

### 💫 Modern UI
- Neo-tech/cyberpunk theme
- Neon colors and glowing effects
- Dark mode optimized
- Smooth animations
- Responsive design

## Technology Stack

- **Backend**: Flask + Python
- **Map**: Leaflet.js
- **Charts**: Chart.js
- **Fonts**: Orbitron, Rajdhani
- **Icons**: Font Awesome
- **ML**: EWMA prediction algorithm
- **Routing**: Greedy nearest-neighbor

## Installation

```bash
# Install dependencies (from backend directory)
cd backend
source .venv/bin/activate
pip install flask flask-cors pandas
```

## Running the Application

```bash
# From the frontend directory
cd /Users/nbal0029/Desktop/IoT/cleanroute-backend/frontend
source ../backend/.venv/bin/activate
python app.py
```

The application will start at: **http://localhost:5000**

## Usage Guide

### 1. View Current Bin Status
- Map loads with all bins displayed
- Colors indicate fill levels:
  - 🟢 Green: < 70% (Normal)
  - 🟠 Orange: 70-90% (Warning)
  - 🔴 Red: > 90% (Critical)
  - ⚫ Gray: Offline

### 2. Generate ML Predictions
1. Select a **Prediction Date** (defaults to tomorrow)
2. Select a **Prediction Time** (defaults to 2:00 PM)
3. Click **"Generate Predictions"**
4. Map markers update with predicted fill levels
5. Markers show predicted percentages

### 3. Optimize Collection Route
1. Set prediction date/time (or use existing predictions)
2. Click **"Optimize Route"**
3. Route displays on map with numbered waypoints
4. Route panel shows:
   - Number of bins to collect
   - Total distance (km)
   - Estimated time (hours)
   - Step-by-step waypoints

### 4. View Bin Details
1. Click any bin marker on map
2. Popup shows basic info
3. Click **"View Details"** button
4. Modal opens with:
   - Current fill level, battery, capacity, status
   - 30-day history chart

### 5. Reset View
- Click **"Reset View"** to:
  - Clear route visualization
  - Reset map zoom
  - Reload current bin data

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/bins` | GET | Get all bins with current status |
| `/api/bins/{id}/history` | GET | Get 30-day history for specific bin |
| `/api/predictions/{time}` | GET | Get ML predictions for target time |
| `/api/route/{time}` | GET | Get optimized collection route |
| `/api/stats` | GET | Get system-wide statistics |

## UI Components

### Header
- Logo with animated recycle icon
- Real-time statistics bar
- Auto-updating metrics

### Sidebar
- Date/time picker for predictions
- Action buttons (Predict, Optimize, Reset)
- Route information panel
- Legend for marker colors

### Map
- Full-screen interactive map
- Custom styled markers
- Route visualization
- Popup windows

### Modal
- Detailed bin information
- Historical fill level chart
- Responsive design

## Color Scheme

```css
Neon Cyan:   #00ffff
Neon Green:  #00ff88
Neon Pink:   #ff0055
Neon Orange: #ffaa00
Neon Blue:   #0099ff
Dark BG:     #0a0a0f
```

## File Structure

```
frontend/
├── app.py                 # Flask server with API routes
├── static/
│   ├── css/
│   │   └── style.css     # Neo-tech theme styles
│   └── js/
│       └── app.js        # Frontend logic
└── templates/
    └── index.html        # Main HTML template
```

## Mock Data

The frontend reads from CSV files in `backend/mock_data/`:
- `bins_config.csv` - 30 bins with real Colombo locations
- `telemetry_data.csv` - 30 days of historical data (5400 records)

## Browser Compatibility

- Chrome/Edge: ✅ Fully supported
- Firefox: ✅ Fully supported
- Safari: ✅ Fully supported
- Mobile: ✅ Responsive design

## Performance

- Map renders 30 bins instantly
- Predictions calculated in < 2 seconds
- Route optimization in < 3 seconds
- Stats refresh every 30 seconds
- No database required (CSV-based)

## Customization

### Change Map Center
Edit `app.js` line 10:
```javascript
map.setView([6.9271, 79.8612], 12); // [lat, lng], zoom
```

### Change Collection Threshold
Edit `app.py` route optimization (line 190):
```python
if prediction['predicted_fill_level'] >= 70:  # Change threshold
```

### Change Color Scheme
Edit `style.css` `:root` section to modify neon colors

## Troubleshooting

**Map not loading?**
- Check internet connection (uses CDN for Leaflet tiles)
- Verify Flask server is running on port 5000

**Predictions failing?**
- Ensure CSV files exist in `backend/mock_data/`
- Check console for error messages
- Verify date format is valid

**Route not displaying?**
- Run predictions first before optimizing route
- Ensure some bins are predicted > 70% full
- Check browser console for errors

## Future Enhancements

- Real-time WebSocket updates
- Historical route playback
- Multi-day route planning
- Weather integration
- Traffic-aware routing
- Export routes to PDF/Excel
- Mobile app version
- Push notifications for critical bins

## Credits

Developed for IoT Waste Management System
Using ML predictions (EWMA) and route optimization (Greedy NN)
