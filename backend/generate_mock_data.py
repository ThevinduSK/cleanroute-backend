#!/usr/bin/env python3
"""
Mock Data Generator for CleanRoute System

Generates realistic telemetry data for 30 bins across Colombo with:
- Real GPS coordinates from Colombo landmarks
- Realistic fill patterns based on location type
- 30 days of historical data
- Edge cases (battery low, offline, erratic data)
- CSV export for ML model training
"""
import os
import sys
import random
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import psycopg2
from psycopg2.extras import execute_batch
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

API_BASE_URL = "http://localhost:8000"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "cleanroute_db",
    "user": "cleanroute_user",
    "password": "cleanroute_pass"
}

DAYS_OF_HISTORY = 30
HOURS_BETWEEN_READINGS = 4  # Telemetry every 4 hours
CSV_OUTPUT_DIR = "mock_data"

# ─────────────────────────────────────────────────────────────────────────────
# Real Colombo GPS Coordinates
# ─────────────────────────────────────────────────────────────────────────────

BIN_LOCATIONS = [
    # Zone 1: Fort & Pettah (Commercial - High Traffic)
    {"id": "B001", "lat": 6.9344, "lon": 79.8428, "type": "commercial", "name": "Fort Railway Station"},
    {"id": "B002", "lat": 6.9349, "lon": 79.8538, "type": "commercial", "name": "Pettah Market"},
    {"id": "B003", "lat": 6.9318, "lon": 79.8478, "type": "commercial", "name": "Manning Market"},
    {"id": "B004", "lat": 6.9295, "lon": 79.8445, "type": "commercial", "name": "World Trade Center"},
    
    # Zone 2: Slave Island & Cinnamon Gardens (Mixed)
    {"id": "B005", "lat": 6.9214, "lon": 79.8533, "type": "park", "name": "Beira Lake"},
    {"id": "B006", "lat": 6.9271, "lon": 79.8612, "type": "mixed", "name": "Independence Square"},
    {"id": "B007", "lat": 6.9197, "lon": 79.8553, "type": "park", "name": "National Museum"},
    {"id": "B008", "lat": 6.9147, "lon": 79.8731, "type": "park", "name": "Viharamahadevi Park"},
    
    # Zone 3: Bambalapitiya & Wellawatta (Residential)
    {"id": "B009", "lat": 6.8942, "lon": 79.8553, "type": "residential", "name": "Bambalapitiya Junction"},
    {"id": "B010", "lat": 6.8868, "lon": 79.8572, "type": "residential", "name": "Wellawatta Beach"},
    {"id": "B011", "lat": 6.8795, "lon": 79.8593, "type": "residential", "name": "Dehiwala Junction"},
    {"id": "B012", "lat": 6.8912, "lon": 79.8531, "type": "residential", "name": "Railway Avenue"},
    
    # Zone 4: Kollupitiya & Colpetty (High-End)
    {"id": "B013", "lat": 6.9103, "lon": 79.8500, "type": "commercial", "name": "Kollupitiya Market"},
    {"id": "B014", "lat": 6.9185, "lon": 79.8475, "type": "commercial", "name": "Liberty Plaza"},
    {"id": "B015", "lat": 6.9089, "lon": 79.8565, "type": "park", "name": "Galle Face North"},
    {"id": "B016", "lat": 6.9045, "lon": 79.8580, "type": "park", "name": "Galle Face South"},
    
    # Zone 5: Mount Lavinia (Coastal)
    {"id": "B017", "lat": 6.8372, "lon": 79.8631, "type": "residential", "name": "Mount Lavinia Beach"},
    {"id": "B018", "lat": 6.8425, "lon": 79.8610, "type": "residential", "name": "Golden Mile Beach"},
    {"id": "B019", "lat": 6.8315, "lon": 79.8645, "type": "residential", "name": "Hotel Road"},
    
    # Zone 6: Nugegoda & Maharagama (Suburban)
    {"id": "B020", "lat": 6.8654, "lon": 79.8896, "type": "suburban", "name": "Nugegoda Junction"},
    {"id": "B021", "lat": 6.8532, "lon": 79.9102, "type": "suburban", "name": "Maharagama Junction"},
    {"id": "B022", "lat": 6.8701, "lon": 79.8965, "type": "suburban", "name": "Nawala Junction"},
    
    # Zone 7: Rajagiriya & Battaramulla (IT/Commercial)
    {"id": "B023", "lat": 6.9145, "lon": 79.9010, "type": "commercial", "name": "Rajagiriya Junction"},
    {"id": "B024", "lat": 6.9012, "lon": 79.9189, "type": "park", "name": "Battaramulla Lake"},
    {"id": "B025", "lat": 6.9098, "lon": 79.8875, "type": "suburban", "name": "Kotte Road"},
    
    # Zone 8: Dehiwala & Ratmalana (Mixed)
    {"id": "B026", "lat": 6.8543, "lon": 79.8654, "type": "residential", "name": "Zoo Area"},
    {"id": "B027", "lat": 6.8412, "lon": 79.8798, "type": "mixed", "name": "Ratmalana Airport"},
    {"id": "B028", "lat": 6.8498, "lon": 79.8721, "type": "residential", "name": "Kalubowila Hospital"},
    
    # Zone 9: Borella & Maradana (Transit)
    {"id": "B029", "lat": 6.9183, "lon": 79.8687, "type": "residential", "name": "Borella Junction"},
    {"id": "B030", "lat": 6.9319, "lon": 79.8650, "type": "commercial", "name": "Maradana Station"},
]

# Fill rates per hour by bin type
FILL_RATES = {
    "commercial": (3.0, 5.0),    # 3-5% per hour
    "residential": (1.0, 2.0),   # 1-2% per hour
    "park": (1.5, 3.0),          # 1.5-3% per hour
    "suburban": (0.5, 1.5),      # 0.5-1.5% per hour
    "mixed": (2.0, 4.0),         # 2-4% per hour
}

# Edge case bins
EDGE_CASES = {
    "battery_low": ["B007", "B019"],      # Low battery (3.3V, 3.4V)
    "offline": ["B025"],                   # Offline (90 min no data)
    "erratic": ["B011"],                   # Erratic sensor data
    "perfect": ["B006"],                   # Clean reference data
    "just_emptied": ["B004"],              # Recently emptied
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_fill_rate(bin_type: str, hour: int, day_of_week: int) -> float:
    """Get fill rate for bin based on type, time of day, and day of week."""
    base_min, base_max = FILL_RATES[bin_type]
    base_rate = random.uniform(base_min, base_max)
    
    # Time of day multiplier
    if 0 <= hour < 6:       # Night (low)
        multiplier = 0.3
    elif 6 <= hour < 12:    # Morning (normal)
        multiplier = 1.0
    elif 12 <= hour < 18:   # Afternoon (peak)
        multiplier = 1.5
    else:                   # Evening (moderate)
        multiplier = 1.2
    
    # Day of week variation (0=Monday, 6=Sunday)
    if day_of_week in [5, 6]:  # Weekend - higher for commercial/parks
        if bin_type in ["commercial", "park"]:
            multiplier *= 1.3
        else:
            multiplier *= 0.8
    
    # Random daily variation (±20%)
    daily_variation = random.uniform(0.8, 1.2)
    
    return base_rate * multiplier * daily_variation


def add_sensor_noise(value: float, noise_pct: float = 2.0) -> float:
    """Add realistic sensor noise."""
    noise = random.uniform(-noise_pct, noise_pct)
    return max(0, min(100, value + noise))


def generate_user_data(bin_id: str) -> Dict[str, str]:
    """Generate realistic user data for bin."""
    user_names = [
        "Pradeep Silva", "Nimal Fernando", "Kumari Perera", "Sunil Jayawardena",
        "Chaminda Rodrigo", "Dilshan Gunawardena", "Tharindu Wijesinghe",
        "Sachini Mendis", "Ruwan Dissanayake", "Malini Rathnayake"
    ]
    
    user_id = f"USER{int(bin_id[1:]):03d}"
    user_name = random.choice(user_names)
    user_phone = f"+9477{random.randint(1000000, 9999999)}"
    wifi_ssid = f"WiFi_{bin_id}"
    
    return {
        "user_id": user_id,
        "user_name": user_name,
        "user_phone": user_phone,
        "wifi_ssid": wifi_ssid
    }


# ─────────────────────────────────────────────────────────────────────────────
# Data Generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_historical_telemetry(bin_config: Dict, days: int = 30) -> List[Dict]:
    """Generate realistic historical telemetry data for one bin."""
    records = []
    
    bin_id = bin_config["id"]
    bin_type = bin_config["type"]
    
    # Starting conditions with more variability
    current_fill = random.uniform(10, 40)
    battery = random.uniform(3.8, 4.2)  # Variable starting battery
    last_emptied = None
    
    # Each bin gets unique fill pattern multiplier
    bin_multiplier = random.uniform(0.7, 1.3)
    
    # Generate data points
    start_time = datetime.utcnow() - timedelta(days=days)
    num_readings = (days * 24) // HOURS_BETWEEN_READINGS
    
    for i in range(num_readings):
        timestamp = start_time + timedelta(hours=i * HOURS_BETWEEN_READINGS)
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        
        # Calculate fill increase with more variability
        fill_rate = get_fill_rate(bin_type, hour, day_of_week)
        fill_increase = fill_rate * HOURS_BETWEEN_READINGS * bin_multiplier
        
        # Add random events (heavy usage spikes)
        if random.random() < 0.05:  # 5% chance of spike
            fill_increase *= random.uniform(1.5, 2.5)
        
        current_fill += fill_increase
        
        # Add sensor noise
        noisy_fill = add_sensor_noise(current_fill)
        
        # Handle special cases
        if bin_id in EDGE_CASES["erratic"]:
            # Add extra noise for erratic bin
            noisy_fill = add_sensor_noise(current_fill, noise_pct=5.0)
        
        # Check if needs emptying (variable threshold)
        emptied = False
        empty_threshold = random.uniform(82, 97)
        if current_fill >= empty_threshold:
            current_fill = random.uniform(8, 25)
            noisy_fill = current_fill
            emptied = True
            last_emptied = timestamp
        
        # Battery decay (more realistic)
        battery_drain = random.uniform(0.015, 0.025) / (num_readings / days)
        battery -= battery_drain
        battery = max(battery, 3.2)
        
        # Temperature (daily cycle with day-to-day variation)
        base_temp = 28 + random.uniform(-2, 3)  # Day-to-day variation
        temp_variation = 6 * (1 - abs(hour - 14) / 14)  # Peak at 2 PM
        temp = base_temp + temp_variation + random.uniform(-1.5, 1.5)
        
        record = {
            "ts": timestamp.isoformat(),
            "bin_id": bin_id,
            "fill_pct": round(noisy_fill, 1),
            "batt_v": round(battery + random.uniform(-0.08, 0.08), 2),
            "temp_c": round(temp, 1),
            "emptied": emptied,
            "lat": bin_config["lat"],
            "lon": bin_config["lon"]
        }
        
        records.append(record)
    
    return records


def apply_edge_cases(all_records: List[Dict]) -> List[Dict]:
    """Apply special edge case scenarios."""
    
    # Battery low cases
    for bin_id in EDGE_CASES["battery_low"]:
        target_voltage = 3.3 if bin_id == "B007" else 3.4
        for record in all_records:
            if record["bin_id"] == bin_id:
                # Set battery to low but add small variation
                record["batt_v"] = round(target_voltage + random.uniform(-0.05, 0.05), 2)
    
    # Just emptied case
    for bin_id in EDGE_CASES["just_emptied"]:
        # Find recent records and set low fill
        recent_count = 0
        for record in reversed(all_records):
            if record["bin_id"] == bin_id and recent_count < 5:
                record["fill_pct"] = round(random.uniform(10, 15), 1)
                record["emptied"] = True if recent_count == 4 else False
                recent_count += 1
    
    return all_records


# ─────────────────────────────────────────────────────────────────────────────
# CSV Export/Import
# ─────────────────────────────────────────────────────────────────────────────

def export_to_csv(records: List[Dict], filename: str = "telemetry_data.csv"):
    """Export telemetry data to CSV file."""
    os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(CSV_OUTPUT_DIR, filename)
    
    if not records:
        print("⚠️  No records to export")
        return filepath
    
    # Write CSV
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = ["ts", "bin_id", "fill_pct", "batt_v", "temp_c", "emptied", "lat", "lon"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for record in records:
            writer.writerow(record)
    
    print(f"✅ Exported {len(records)} records to {filepath}")
    return filepath


def export_bins_to_csv(bins: List[Dict], filename: str = "bins_config.csv"):
    """Export bin configurations to CSV."""
    os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(CSV_OUTPUT_DIR, filename)
    
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = ["id", "lat", "lon", "type", "name"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for bin_config in bins:
            writer.writerow(bin_config)
    
    print(f"✅ Exported {len(bins)} bin configs to {filepath}")
    return filepath


# ─────────────────────────────────────────────────────────────────────────────
# Database Operations
# ─────────────────────────────────────────────────────────────────────────────

def register_bins_via_api():
    """Register bins using API endpoint."""
    print("\n📝 Registering bins via API...")
    
    registered = 0
    for bin_config in BIN_LOCATIONS:
        user_data = generate_user_data(bin_config["id"])
        
        payload = {
            "bin_id": bin_config["id"],
            "user_id": user_data["user_id"],
            "user_name": user_data["user_name"],
            "user_phone": user_data["user_phone"],
            "wifi_ssid": user_data["wifi_ssid"],
            "lat": bin_config["lat"],
            "lon": bin_config["lon"]
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/devices/register", json=payload, timeout=5)
            if response.status_code == 200:
                registered += 1
            else:
                print(f"⚠️  Failed to register {bin_config['id']}: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Error registering {bin_config['id']}: {e}")
    
    print(f"✅ Registered {registered}/{len(BIN_LOCATIONS)} bins")
    return registered


def insert_telemetry_to_db(records: List[Dict]):
    """Insert telemetry records directly into database (fast)."""
    print(f"\n📥 Inserting {len(records)} telemetry records to database...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Prepare data for batch insert
        insert_query = """
            INSERT INTO telemetry (ts, bin_id, fill_pct, batt_v, temp_c, emptied, lat, lon)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = [
            (r["ts"], r["bin_id"], r["fill_pct"], r["batt_v"], 
             r["temp_c"], r["emptied"], r["lat"], r["lon"])
            for r in records
        ]
        
        # Batch insert for speed
        execute_batch(cur, insert_query, data, page_size=100)
        conn.commit()
        
        print(f"✅ Inserted {len(records)} records successfully")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        raise


def setup_offline_bin():
    """Set last_seen for offline bin to 90 minutes ago."""
    print("\n🔌 Setting up offline bin scenario...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        offline_time = datetime.utcnow() - timedelta(minutes=90)
        
        for bin_id in EDGE_CASES["offline"]:
            cur.execute(
                "UPDATE bins SET last_seen = %s, device_status = 'offline' WHERE bin_id = %s",
                (offline_time, bin_id)
            )
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Set {EDGE_CASES['offline']} as offline")
        
    except Exception as e:
        print(f"⚠️  Error setting offline bin: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Main Generation
# ─────────────────────────────────────────────────────────────────────────────

def print_header():
    """Print script header."""
    print("\n" + "="*70)
    print("  CleanRoute Mock Data Generator")
    print("  Real Colombo Locations | 30 Bins | 30 Days History")
    print("="*70)


def print_summary(total_records: int):
    """Print generation summary."""
    print("\n" + "="*70)
    print("  📊 GENERATION COMPLETE")
    print("="*70)
    
    print(f"\n✅ Bins created: {len(BIN_LOCATIONS)}")
    print(f"✅ Telemetry records: {total_records:,}")
    print(f"✅ Time range: {DAYS_OF_HISTORY} days")
    print(f"✅ CSV files exported to: {CSV_OUTPUT_DIR}/")
    
    # Bin type distribution
    type_counts = {}
    for bin_config in BIN_LOCATIONS:
        bin_type = bin_config["type"]
        type_counts[bin_type] = type_counts.get(bin_type, 0) + 1
    
    print("\n📍 Bin Type Distribution:")
    for bin_type, count in sorted(type_counts.items()):
        print(f"   • {bin_type.capitalize()}: {count} bins")
    
    print("\n⚠️  Edge Cases Configured:")
    print(f"   • Battery low: {len(EDGE_CASES['battery_low'])} bins {EDGE_CASES['battery_low']}")
    print(f"   • Offline: {len(EDGE_CASES['offline'])} bin {EDGE_CASES['offline']}")
    print(f"   • Erratic data: {len(EDGE_CASES['erratic'])} bin {EDGE_CASES['erratic']}")
    print(f"   • Just emptied: {len(EDGE_CASES['just_emptied'])} bin {EDGE_CASES['just_emptied']}")
    
    print("\n🚀 Next Steps:")
    print("   1. Test predictions:")
    print('      curl "http://localhost:8000/bins/forecast?target_time=tomorrow_afternoon"')
    print("\n   2. Generate route:")
    print("      python test_ml_routing.py")
    print("\n   3. Run full test suite:")
    print("      python backend/test_ml_routing.py")
    
    print("\n" + "="*70 + "\n")


def main():
    """Main generation workflow."""
    print_header()
    
    # Step 1: Export bin configurations to CSV
    print("\n📝 Step 1: Exporting bin configurations...")
    export_bins_to_csv(BIN_LOCATIONS)
    
    # Step 2: Generate historical telemetry data
    print(f"\n🔄 Step 2: Generating {DAYS_OF_HISTORY} days of telemetry data...")
    all_records = []
    
    for i, bin_config in enumerate(BIN_LOCATIONS, 1):
        print(f"   Generating data for {bin_config['id']} ({i}/{len(BIN_LOCATIONS)})...", end="\r")
        records = generate_historical_telemetry(bin_config, DAYS_OF_HISTORY)
        all_records.extend(records)
    
    print(f"   ✅ Generated {len(all_records):,} telemetry records for {len(BIN_LOCATIONS)} bins")
    
    # Step 3: Apply edge cases
    print("\n⚙️  Step 3: Applying edge case scenarios...")
    all_records = apply_edge_cases(all_records)
    
    # Step 4: Export telemetry to CSV
    print("\n💾 Step 4: Exporting telemetry to CSV...")
    csv_path = export_to_csv(all_records)
    
    # Step 5: Register bins via API
    try:
        registered = register_bins_via_api()
        if registered == 0:
            print("\n⚠️  Warning: Could not register bins via API.")
            print("    Make sure backend server is running:")
            print("    cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000")
            return
    except Exception as e:
        print(f"\n❌ Error connecting to API: {e}")
        print("    Make sure backend server is running!")
        return
    
    # Step 6: Insert telemetry to database
    insert_telemetry_to_db(all_records)
    
    # Step 7: Set up offline bin
    setup_offline_bin()
    
    # Step 8: Print summary
    print_summary(len(all_records))


if __name__ == "__main__":
    main()
