# Mock Data Generation Guide

## 🎯 Overview

This guide explains how to generate and use realistic mock data for testing the CleanRoute ML prediction and route optimization system.

**What it does:**
- ✅ Creates 30 bins with **real Colombo GPS coordinates**
- ✅ Generates 30 days of **realistic historical telemetry** (~4,500 records)
- ✅ Exports data to **CSV files** for ML model training
- ✅ Inserts data into **PostgreSQL database** for API testing
- ✅ Includes **edge cases** (battery low, offline, erratic data)

---

## 🚀 Quick Start

### Prerequisites:
```bash
# 1. PostgreSQL running
sudo systemctl status postgresql

# 2. Backend server running
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. Required Python packages (already in requirements.txt)
pip install psycopg2-binary requests
```

### Generate Mock Data:
```bash
cd backend
python generate_mock_data.py
```

**Expected output:**
```
======================================================================
  CleanRoute Mock Data Generator
  Real Colombo Locations | 30 Bins | 30 Days History
======================================================================

📝 Step 1: Exporting bin configurations...
✅ Exported 30 bin configs to mock_data/bins_config.csv

🔄 Step 2: Generating 30 days of telemetry data...
   ✅ Generated 4,500 telemetry records for 30 bins

⚙️  Step 3: Applying edge case scenarios...

💾 Step 4: Exporting telemetry to CSV...
✅ Exported 4500 records to mock_data/telemetry_data.csv

📝 Step 5: Registering bins via API...
✅ Registered 30/30 bins

📥 Step 6: Inserting telemetry to database...
✅ Inserted 4,500 records successfully

🔌 Step 7: Setting up offline bin scenario...
✅ Set ['B025'] as offline

======================================================================
  📊 GENERATION COMPLETE
======================================================================

✅ Bins created: 30
✅ Telemetry records: 4,500
✅ Time range: 30 days
✅ CSV files exported to: mock_data/
```

---

## 📁 Generated Files

### `mock_data/bins_config.csv`
Contains bin configurations with real Colombo locations:

```csv
id,lat,lon,type,name
B001,6.9344,79.8428,commercial,Fort Railway Station
B002,6.9349,79.8538,commercial,Pettah Market
B003,6.9318,79.8478,commercial,Manning Market
...
```

**Fields:**
- `id`: Bin identifier (B001-B030)
- `lat`, `lon`: Real GPS coordinates in Colombo
- `type`: commercial, residential, park, suburban, mixed
- `name`: Landmark/location name

---

### `mock_data/telemetry_data.csv`
Contains historical telemetry data:

```csv
ts,bin_id,fill_pct,batt_v,temp_c,emptied,lat,lon
2025-11-13T00:00:00,B001,23.5,4.18,28.3,False,6.9344,79.8428
2025-11-13T04:00:00,B001,31.2,4.17,26.8,False,6.9344,79.8428
2025-11-13T08:00:00,B001,39.7,4.16,30.5,False,6.9344,79.8428
...
```

**Fields:**
- `ts`: Timestamp (ISO format)
- `bin_id`: Bin identifier
- `fill_pct`: Fill percentage (0-100)
- `batt_v`: Battery voltage (3.2-4.2V)
- `temp_c`: Temperature in Celsius
- `emptied`: Boolean flag (True when bin was emptied)
- `lat`, `lon`: GPS coordinates

---

## 🗺️ Bin Locations (30 Real Colombo Sites)

### Geographic Distribution:

**Zone 1: Fort & Pettah (Commercial)**
- B001: Fort Railway Station (6.9344, 79.8428)
- B002: Pettah Market (6.9349, 79.8538)
- B003: Manning Market (6.9318, 79.8478)
- B004: World Trade Center (6.9295, 79.8445)

**Zone 2: Cinnamon Gardens (Mixed)**
- B005: Beira Lake (6.9214, 79.8533)
- B006: Independence Square (6.9271, 79.8612) ← **Depot**
- B007: National Museum (6.9197, 79.8553)
- B008: Viharamahadevi Park (6.9147, 79.8731)

**Zone 3: Bambalapitiya/Wellawatta (Residential)**
- B009: Bambalapitiya Junction (6.8942, 79.8553)
- B010: Wellawatta Beach (6.8868, 79.8572)
- B011: Dehiwala Junction (6.8795, 79.8593)
- B012: Railway Avenue (6.8912, 79.8531)

**Zone 4: Kollupitiya (High-End)**
- B013: Kollupitiya Market (6.9103, 79.8500)
- B014: Liberty Plaza (6.9185, 79.8475)
- B015: Galle Face North (6.9089, 79.8565)
- B016: Galle Face South (6.9045, 79.8580)

**Zone 5: Mount Lavinia (Coastal)**
- B017: Mount Lavinia Beach (6.8372, 79.8631)
- B018: Golden Mile Beach (6.8425, 79.8610)
- B019: Hotel Road (6.8315, 79.8645)

**Zone 6: Nugegoda/Maharagama (Suburban)**
- B020: Nugegoda Junction (6.8654, 79.8896)
- B021: Maharagama Junction (6.8532, 79.9102)
- B022: Nawala Junction (6.8701, 79.8965)

**Zone 7: Rajagiriya/Battaramulla (IT Zone)**
- B023: Rajagiriya Junction (6.9145, 79.9010)
- B024: Battaramulla Lake (6.9012, 79.9189)
- B025: Kotte Road (6.9098, 79.8875)

**Zone 8: Dehiwala/Ratmalana (Mixed)**
- B026: Zoo Area (6.8543, 79.8654)
- B027: Ratmalana Airport (6.8412, 79.8798)
- B028: Kalubowila Hospital (6.8498, 79.8721)

**Zone 9: Borella/Maradana (Transit)**
- B029: Borella Junction (6.9183, 79.8687)
- B030: Maradana Station (6.9319, 79.8650)

**Coverage:** ~10km North-South, ~7km East-West

---

## 📊 Data Characteristics

### Fill Rates by Bin Type:

| Bin Type | Fill Rate (% per hour) | Examples |
|----------|------------------------|----------|
| Commercial | 3-5% | Markets, stations, offices |
| Residential | 1-2% | Neighborhoods, apartments |
| Park/Public | 1.5-3% | Parks, beaches, public spaces |
| Suburban | 0.5-1.5% | Low-density residential |
| Mixed | 2-4% | Variable usage patterns |

### Realistic Patterns:

1. **Daily Cycles:**
   - Night (00:00-06:00): 30% of base rate (low activity)
   - Morning (06:00-12:00): 100% of base rate (normal)
   - Afternoon (12:00-18:00): 150% of base rate (peak)
   - Evening (18:00-24:00): 120% of base rate (moderate)

2. **Emptying Events:**
   - Triggered when fill reaches 85-95%
   - Reset to 10-20% (realistic emptying)
   - Frequency: Every 3-7 days (varies by bin type)
   - `emptied` flag set to `True`

3. **Sensor Characteristics:**
   - Fill level noise: ±2% variation
   - Battery decay: 4.2V → 3.6V over 30 days
   - Temperature: 25-35°C with daily cycle
   - Data points: Every 4 hours (~180 per bin)

---

## ⚠️ Edge Cases Included

### 1. Battery Low (2 bins):
- **B007** (National Museum): 3.3V (critical)
- **B019** (Hotel Road): 3.4V (warning)
- Should trigger battery_low alerts

### 2. Offline Bin (1 bin):
- **B025** (Kotte Road): Last seen 90 minutes ago
- Should trigger device_offline alert
- Should be excluded from route optimization

### 3. Erratic Data (1 bin):
- **B011** (Dehiwala): ±5% noise (unreliable sensor)
- EWMA should smooth out the noise
- Lower confidence score

### 4. Just Emptied (1 bin):
- **B004** (World Trade Center): Recently emptied (12% fill)
- Should NOT appear in tomorrow's collection route

### 5. Perfect Data (1 bin):
- **B006** (Independence Square): Clean, consistent pattern
- High confidence predictions
- Reference bin for comparison

---

## 🧪 Testing the Mock Data

### 1. Verify Data in Database:
```bash
# Check bins registered
curl http://localhost:8000/bins/latest | jq

# Check specific bin
curl http://localhost:8000/bins/B001/prediction?target_time=tomorrow_afternoon | jq
```

### 2. Test ML Predictions:
```bash
# Forecast for tomorrow afternoon
curl "http://localhost:8000/bins/forecast?target_time=tomorrow_afternoon&threshold=80" | jq

# Expected: 11-13 bins will need collection
```

### 3. Test Route Optimization:
```bash
# Generate optimal route
curl -X POST http://localhost:8000/routes/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "target_time": "tomorrow_afternoon",
    "threshold_pct": 80
  }' | jq

# Expected: Route with 11-13 bins, 40-55km distance
```

### 4. Test Alerts:
```bash
# Run health check
curl -X POST http://localhost:8000/monitoring/health-check | jq

# Expected alerts:
# - battery_low: 2 (B007, B019)
# - device_offline: 1 (B025)
# - overflow_risk: 3-5 bins
```

### 5. Run Full Test Suite:
```bash
cd backend
python test_ml_routing.py
```

---

## 🔧 Using CSV Data for ML Training

### Option 1: Use Database (Default)
```bash
# Data automatically loaded from PostgreSQL
python test_ml_routing.py
```

### Option 2: Use CSV Files
```bash
# Set environment variable to use CSV
export USE_CSV_DATA=true

# Now ML model will read from CSV instead of database
python test_ml_routing.py
```

### When to Use CSV:
- ✅ Training ML models offline
- ✅ Testing without database
- ✅ Analyzing historical patterns
- ✅ Exporting data for visualization tools
- ✅ Sharing data with team members

---

## 📈 Expected Test Results

### Current State (Today 2:00 PM):
```
Critical (>90%):     3 bins  (B002, B012, B023)
High (80-90%):       5 bins  (B001, B009, B015, B018, B030)
Medium (50-80%):    12 bins
Low (<50%):         10 bins
```

### Predicted Tomorrow Afternoon:
```
Need collection (≥80%): 11-13 bins
Route distance:         40-55 km
Route duration:         3-4 hours
Confidence:             High (8 bins), Medium (3-5 bins)
```

### Route Should:
- ✅ Start at Independence Square (depot)
- ✅ Visit Fort/Pettah cluster (close together)
- ✅ Move to coastal bins (Wellawatta, Mount Lavinia)
- ✅ Visit inland bins (Rajagiriya)
- ✅ Return to depot
- ❌ NOT visit offline bin B025

---

## 🔄 Regenerating Data

### Full Regeneration:
```bash
# Delete existing data
psql cleanroute_db -c "DELETE FROM telemetry; DELETE FROM bins;"

# Generate fresh data
python generate_mock_data.py
```

### Modify Parameters:
Edit `generate_mock_data.py`:
```python
# Change number of bins (line 28-57)
BIN_LOCATIONS = [...]  # Add/remove bins

# Change history window (line 19)
DAYS_OF_HISTORY = 30  # Change to 7, 60, 90, etc.

# Change data frequency (line 20)
HOURS_BETWEEN_READINGS = 4  # Change to 2, 6, 12, etc.

# Change fill rates (line 87-93)
FILL_RATES = {
    "commercial": (3.0, 5.0),  # Adjust ranges
    ...
}
```

---

## 📊 Data Analysis Tips

### View CSV in Python:
```python
import pandas as pd

# Load bin configs
bins = pd.read_csv('mock_data/bins_config.csv')
print(bins.groupby('type').size())

# Load telemetry
telemetry = pd.read_csv('mock_data/telemetry_data.csv')
telemetry['ts'] = pd.to_datetime(telemetry['ts'])

# Analyze fill rates
bin_stats = telemetry.groupby('bin_id')['fill_pct'].agg(['mean', 'std', 'min', 'max'])
print(bin_stats)
```

### Visualize on Map:
```python
import folium

bins = pd.read_csv('mock_data/bins_config.csv')

# Create map centered on Colombo
m = folium.Map(location=[6.9271, 79.8612], zoom_start=12)

# Add markers
for _, bin in bins.iterrows():
    folium.Marker(
        [bin['lat'], bin['lon']],
        popup=f"{bin['id']}: {bin['name']}",
        tooltip=bin['type']
    ).add_to(m)

m.save('colombo_bins.html')
```

---

## 🆘 Troubleshooting

### Issue: "Connection refused" error
**Solution:** Make sure backend server is running:
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Issue: "Database connection error"
**Solution:** Check PostgreSQL is running and credentials are correct:
```bash
sudo systemctl status postgresql
psql -U cleanroute_user -d cleanroute_db -h localhost
```

### Issue: No predictions generated
**Solution:** Verify data was inserted:
```bash
psql cleanroute_db -c "SELECT COUNT(*) FROM telemetry;"
# Should show ~4,500 records
```

### Issue: CSV files not found
**Solution:** Check `mock_data/` directory was created:
```bash
ls -la mock_data/
# Should show bins_config.csv and telemetry_data.csv
```

---

## 🎯 Next Steps

1. **Generate mock data** (you are here)
2. **Test predictions:** `curl http://localhost:8000/bins/forecast?target_time=tomorrow_afternoon`
3. **Test routing:** `python test_ml_routing.py`
4. **Build frontend:** Display bins and routes on map
5. **Deploy to production:** Use real sensor data

---

**Questions? Check the main documentation files or run the test suite!**
