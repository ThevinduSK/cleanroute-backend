# Quick Reference - ML & Routing API

## 🚀 Quick Start

```bash
# 1. Start server (if not running)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Test prediction
curl "http://localhost:8000/bins/forecast?target_time=tomorrow_afternoon&threshold=80"

# 3. Test route optimization
curl -X POST http://localhost:8000/routes/optimize \
  -H "Content-Type: application/json" \
  -d '{"target_time":"tomorrow_afternoon","threshold_pct":80}'

# 4. Run test suite
python test_ml_routing.py
```

---

## 📡 API Endpoints

### 1. Forecast All Bins
```
GET /bins/forecast
  ?target_time=tomorrow_afternoon
  &threshold=80
```

**Time Options:**
- `tomorrow_morning` → Tomorrow 8 AM
- `tomorrow_afternoon` → Tomorrow 2 PM  ⭐ Default
- `6h` → In 6 hours
- `24h` → In 24 hours
- `48h` → In 48 hours
- `2025-12-14T14:00:00Z` → Custom ISO datetime

---

### 2. Predict Single Bin
```
GET /bins/{bin_id}/prediction
  ?target_time=24h
```

---

### 3. Optimize Route ⭐ Main Feature
```
POST /routes/optimize
Body: {
  "target_time": "tomorrow_afternoon",
  "threshold_pct": 80,
  "depot_location": {
    "lat": 6.9271,
    "lon": 79.8612,
    "name": "Municipal Office"
  },
  "algorithm": "greedy"
}
```

---

### 4. Bins At Risk (Legacy)
```
GET /bins/at_risk?threshold_hours=48
```

---

## 🎨 Frontend Integration

### JavaScript Example:
```javascript
// 1. Get predictions
const forecast = await fetch(
  '/bins/forecast?target_time=tomorrow_afternoon&threshold=80'
).then(r => r.json());

console.log(`${forecast.bins_needing_collection} bins need collection`);

// 2. Show on map
forecast.predictions.forEach(bin => {
  if (bin.needs_collection) {
    addMarker(bin.lat, bin.lon, 'red', bin.bin_id);
  }
});

// 3. Generate route
const route = await fetch('/routes/optimize', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    target_time: 'tomorrow_afternoon',
    threshold_pct: 80
  })
}).then(r => r.json());

// 4. Draw route on map
drawPolyline(route.route.path_coordinates);

// 5. Show summary
console.log(`
  Bins: ${route.route.summary.total_bins}
  Distance: ${route.route.summary.total_distance_km} km
  Duration: ${route.route.summary.estimated_duration_min} min
`);
```

---

## 🧮 Response Examples

### Forecast Response:
```json
{
  "target_time": "2025-12-14T14:00:00Z",
  "threshold_pct": 80,
  "predictions": [
    {
      "bin_id": "B001",
      "current_fill": 65.2,
      "predicted_fill": 87.5,
      "needs_collection": true,
      "confidence": "high",
      "lat": 6.9102,
      "lon": 79.8623
    }
  ],
  "total_bins": 50,
  "bins_needing_collection": 12
}
```

### Route Response:
```json
{
  "route": {
    "waypoints": [
      {
        "order": 0,
        "type": "depot",
        "name": "Municipal Office",
        "location": {"lat": 6.9271, "lon": 79.8612}
      },
      {
        "order": 1,
        "type": "bin",
        "bin_id": "B003",
        "predicted_fill": 92.1,
        "location": {"lat": 6.9180, "lon": 79.8600},
        "distance_from_prev_km": 2.3
      }
    ],
    "summary": {
      "total_bins": 12,
      "total_distance_km": 45.2,
      "estimated_duration_min": 150
    },
    "path_coordinates": [[6.9271, 79.8612], ...]
  }
}
```

---

## 🎯 Common Use Cases

### Use Case 1: Plan Tomorrow's Collection
```bash
# See what bins will need collection tomorrow afternoon
curl "http://localhost:8000/bins/forecast?target_time=tomorrow_afternoon&threshold=80"

# Generate route for tomorrow
curl -X POST http://localhost:8000/routes/optimize \
  -H "Content-Type: application/json" \
  -d '{"target_time":"tomorrow_afternoon","threshold_pct":80}'
```

---

### Use Case 2: Emergency Collection (High Fill)
```bash
# Find bins at 90%+ now
curl "http://localhost:8000/bins/forecast?target_time=6h&threshold=90"

# Generate urgent route
curl -X POST http://localhost:8000/routes/optimize \
  -H "Content-Type: application/json" \
  -d '{"target_time":"6h","threshold_pct":90}'
```

---

### Use Case 3: Check Single Bin Status
```bash
# Predict when bin will be full
curl "http://localhost:8000/bins/B001/prediction?target_time=48h"
```

---

## 🔧 Configuration

### Adjust in `ml_prediction.py`:
```python
EWMA_ALPHA = 0.3            # Smoothing (0.1=smooth, 0.5=responsive)
MIN_DATA_POINTS = 5         # Min history needed
MAX_HISTORY_DAYS = 30       # Look back period
```

### Adjust in `route_optimizer.py`:
```python
AVERAGE_SPEED_KMH = 30      # City driving speed
SERVICE_TIME_MINUTES = 5    # Time per bin
DEFAULT_DEPOT = {           # Default start/end
  "lat": 6.9271,
  "lon": 79.8612
}
```

---

## 🧪 Testing

```bash
# Full test suite
python test_ml_routing.py

# Individual endpoint tests
curl http://localhost:8000/bins/forecast?target_time=24h
curl -X POST http://localhost:8000/routes/optimize -d '{"target_time":"24h"}'
```

---

## 📊 Expected Performance

- **Prediction**: 100ms for 50 bins
- **Route optimization**: 50ms for 50 bins
- **Total API response**: <200ms

---

## ⚠️ Edge Cases Handled

✅ Insufficient historical data → Uses current fill
✅ Decreasing fill (emptied) → Uses current fill  
✅ Offline bins → Excluded from route
✅ Missing GPS → Excluded from route
✅ Erratic patterns → EWMA smooths noise
✅ Negative predictions → Capped at current fill

---

## 🎯 Next Steps

1. **Frontend**: Build map UI with Leaflet.js
2. **Testing**: Validate predictions against actual data
3. **Optimization**: Add caching for frequently-used times
4. **Enhancement**: Upgrade to OR-Tools TSP for optimal routes

---

## 📚 Full Documentation

- **Detailed Guide**: `ML_ROUTING_GUIDE.md`
- **Code Comments**: See `ml_prediction.py` and `route_optimizer.py`
- **API Docs**: http://localhost:8000/docs (Swagger UI)

---

**Questions? Run `python test_ml_routing.py` to see it in action!** 🚀
