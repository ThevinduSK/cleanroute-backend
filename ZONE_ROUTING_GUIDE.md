# 🗺️ Zone-Based Route Optimization Guide

## Overview

CleanRoute now supports **zone-based routing**, dividing Colombo into 6 operational zones. Each zone has its own collection route, allowing multiple trucks to operate simultaneously and reducing travel distances.

---

## 🎯 Benefits of Zone-Based Routing

### Traditional Single Route Problems:
- ❌ One truck covers entire city (~45km)
- ❌ Long collection times (~3 hours)
- ❌ Inefficient for large cities
- ❌ No parallel operations

### Zone-Based Solution:
- ✅ Multiple trucks work in parallel
- ✅ Shorter routes per zone (8-12km avg)
- ✅ Faster collection times (45-60 min per zone)
- ✅ Better resource allocation
- ✅ Reduced fuel costs

---

## 📍 Colombo Zone Definitions

### **Zone 1: Fort & Pettah (Commercial)** 🔴
- **Area**: CBD, Railway Station, Manning Market
- **Depot**: Fort Depot (6.9318, 79.8478)
- **Characteristics**: High traffic, commercial waste
- **Color**: Red (#FF6B6B)

### **Zone 2: Slave Island & Kollupitiya (Central)** 🟢
- **Area**: Central business district
- **Depot**: Kollupitiya Depot (6.9185, 79.8475)
- **Characteristics**: Mixed commercial/residential
- **Color**: Teal (#4ECDC4)

### **Zone 3: Galle Face & Bambalapitiya (Coastal)** 🔵
- **Area**: Coastal tourist areas
- **Depot**: Galle Face Depot (6.9045, 79.8580)
- **Characteristics**: Parks, beach areas
- **Color**: Blue (#45B7D1)

### **Zone 4: Wellawatta & Dehiwala (South Residential)** 🟡
- **Area**: Southern residential neighborhoods
- **Depot**: Dehiwala Depot (6.8568, 79.8610)
- **Characteristics**: Residential, beach hotels
- **Color**: Yellow (#F7B731)

### **Zone 5: Nugegoda & Kotte (Suburban East)** 🟣
- **Area**: Eastern suburbs
- **Depot**: Nugegoda Depot (6.8654, 79.8896)
- **Characteristics**: Suburban, mixed use
- **Color**: Purple (#5F27CD)

### **Zone 6: Borella & Maradana (Northeast)** 🔷
- **Area**: Northeastern districts
- **Depot**: Borella Depot (6.9183, 79.8687)
- **Characteristics**: Residential, hospitals
- **Color**: Cyan (#00D2D3)

---

## 🚀 API Endpoints

### 1. Get All Zones
```http
GET /api/zones
```

**Response:**
```json
[
  {
    "id": "zone1",
    "name": "Fort & Pettah (Commercial)",
    "bounds": {
      "lat_min": 6.925,
      "lat_max": 6.940,
      "lon_min": 79.840,
      "lon_max": 79.860
    },
    "depot": {
      "lat": 6.9318,
      "lon": 79.8478,
      "name": "Fort Depot"
    },
    "color": "#FF6B6B"
  },
  ...
]
```

### 2. Get Specific Zone
```http
GET /api/zones/{zone_id}
```

Example: `GET /api/zones/zone1`

### 3. Get Zone-Based Routes
```http
GET /api/route-by-zone/{target_time}
```

Example: `GET /api/route-by-zone/2025-12-14-14-00`

**Response:**
```json
{
  "zones": [
    {
      "zone_id": "zone1",
      "zone_name": "Fort & Pettah (Commercial)",
      "zone_color": "#FF6B6B",
      "depot": {
        "lat": 6.9318,
        "lon": 79.8478,
        "name": "Fort Depot"
      },
      "waypoints": [...],
      "path_coordinates": [[lat, lon], ...],
      "summary": {
        "total_bins": 5,
        "total_distance_km": 8.5,
        "driving_time_min": 17,
        "service_time_min": 25,
        "estimated_duration_min": 42,
        "average_fill_pct": 85.2
      }
    },
    ...
  ],
  "summary": {
    "total_zones": 4,
    "total_bins": 15,
    "total_distance_km": 35.2,
    "total_duration_min": 180
  }
}
```

### 4. Compare: Single Route vs Zone-Based
```http
# Single route (all bins together)
GET /api/route/2025-12-14-14-00

# Zone-based routes (divided by zones)
GET /api/route-by-zone/2025-12-14-14-00
```

---

## 💻 Usage Examples

### PowerShell/Windows
```powershell
# Get all zones
Invoke-RestMethod -Uri http://localhost:5001/api/zones

# Get zone-based routes for tomorrow 2 PM
Invoke-RestMethod -Uri "http://localhost:5001/api/route-by-zone/2025-12-14-14-00"

# Get specific zone info
Invoke-RestMethod -Uri http://localhost:5001/api/zones/zone1
```

### Python
```python
import requests

# Get zone-based routes
response = requests.get('http://localhost:5001/api/route-by-zone/2025-12-14-14-00')
data = response.json()

# Print summary
print(f"Total zones with collections: {data['summary']['total_zones']}")
print(f"Total bins to collect: {data['summary']['total_bins']}")
print(f"Total distance (all zones): {data['summary']['total_distance_km']} km")

# Print each zone
for zone in data['zones']:
    print(f"\n{zone['zone_name']}:")
    print(f"  Bins: {zone['summary']['total_bins']}")
    print(f"  Distance: {zone['summary']['total_distance_km']} km")
    print(f"  Time: {zone['summary']['estimated_duration_min']} min")
```

---

## 📊 How It Works

### 1. **Zone Assignment**
```python
# Bins are automatically assigned to zones based on GPS coordinates
# If a bin is outside all zone boundaries, it's assigned to the nearest zone
```

### 2. **Route Optimization Per Zone**
```python
# Each zone gets its own optimized route
# Uses greedy nearest-neighbor algorithm
# Starts and ends at zone-specific depot
```

### 3. **Parallel Operations**
```python
# Multiple trucks can work simultaneously
# Truck 1: Zone 1 (Fort)
# Truck 2: Zone 3 (Galle Face)
# Truck 3: Zone 4 (Dehiwala)
# etc.
```

---

## 🎨 Frontend Integration

### Displaying Zone Routes on Map

```javascript
// Fetch zone-based routes
fetch('/api/route-by-zone/2025-12-14-14-00')
  .then(response => response.json())
  .then(data => {
    // Draw each zone's route in a different color
    data.zones.forEach(zone => {
      const routeLine = L.polyline(zone.path_coordinates, {
        color: zone.zone_color,
        weight: 4,
        opacity: 0.7
      }).addTo(map);
      
      // Add zone label
      L.marker([zone.depot.lat, zone.depot.lon])
        .bindPopup(`<b>${zone.zone_name}</b><br>
                    ${zone.summary.total_bins} bins<br>
                    ${zone.summary.total_distance_km} km`)
        .addTo(map);
    });
  });
```

---

## 📈 Performance Comparison

### Example: 15 Bins Needing Collection

#### Single Route:
- **Distance**: 45 km
- **Time**: ~180 minutes (3 hours)
- **Trucks**: 1
- **Cost**: Higher fuel, one truck tied up

#### Zone-Based (4 zones):
- **Average per zone**: 10 km
- **Average time per zone**: ~45 minutes
- **Trucks**: 4 (parallel)
- **Total time**: 45 minutes (parallel operation)
- **Cost**: Lower per-truck distance, better utilization

---

## 🔧 Customization

### Adding New Zones

Edit `backend/app/route_optimizer.py`:

```python
COLOMBO_ZONES = {
    "Zone 7 - Custom Area": {
        "id": "zone7",
        "name": "Custom Area Name",
        "bounds": {
            "lat_min": 6.XXX,
            "lat_max": 6.XXX,
            "lon_min": 79.XXX,
            "lon_max": 79.XXX
        },
        "depot": {
            "lat": 6.XXX,
            "lon": 79.XXX,
            "name": "Custom Depot"
        },
        "color": "#HEXCOLOR"
    }
}
```

### Adjusting Zone Boundaries

Modify the `bounds` values in `COLOMBO_ZONES` dictionary to resize zones based on:
- Bin density
- Road network
- Truck capacity
- Collection time windows

---

## 🎯 Best Practices

1. **Zone Size**: Keep zones small enough for 45-60 minute collection times
2. **Balance**: Distribute bins evenly across zones
3. **Depots**: Place depots centrally within each zone
4. **Timing**: Schedule zones to avoid traffic (morning vs evening)
5. **Resources**: Assign appropriate truck capacity per zone

---

## 🧪 Testing

```powershell
# Start the server
.\quickstart.bat

# Test zone endpoints
Invoke-RestMethod http://localhost:5001/api/zones

# Compare single vs zone-based routing
$single = Invoke-RestMethod "http://localhost:5001/api/route/2025-12-14-14-00"
$zones = Invoke-RestMethod "http://localhost:5001/api/route-by-zone/2025-12-14-14-00"

Write-Host "Single Route Distance: $($single.total_distance_km) km"
Write-Host "Zone-Based Total Distance: $($zones.summary.total_distance_km) km"
Write-Host "Number of Zones: $($zones.summary.total_zones)"
```

---

## 📝 Summary

**Zone-based routing provides:**
- ✅ More efficient operations
- ✅ Parallel truck deployment
- ✅ Shorter individual routes
- ✅ Better resource utilization
- ✅ Scalable for larger cities

**Use single-route when:**
- Small number of bins (< 10)
- Single truck operation
- Testing/demo purposes

**Use zone-based when:**
- Large number of bins (> 10)
- Multiple trucks available
- Production deployment
- City-scale operations

---

🎉 **Your CleanRoute system now supports enterprise-grade zone-based routing!**
