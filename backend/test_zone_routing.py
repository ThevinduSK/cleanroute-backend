"""
Test Zone-Based Routing System

This script demonstrates the zone-based routing feature.
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5001"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_get_zones():
    """Test 1: Get all zone definitions"""
    print_section("TEST 1: Get All Zones")
    
    response = requests.get(f"{BASE_URL}/api/zones")
    zones = response.json()
    
    print(f"Total Zones: {len(zones)}\n")
    for zone in zones:
        print(f"📍 {zone['name']}")
        print(f"   ID: {zone['id']}")
        print(f"   Depot: {zone['depot']['name']}")
        print(f"   Color: {zone['color']}")
        print()

def test_zone_routes():
    """Test 2: Get zone-based routes"""
    print_section("TEST 2: Zone-Based Route Optimization")
    
    # Use tomorrow at 2 PM
    target_time = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d-14-00')
    
    response = requests.get(f"{BASE_URL}/api/route-by-zone/{target_time}")
    data = response.json()
    
    if 'zones' in data and data['zones']:
        print(f"🎯 Target Time: {target_time}")
        print(f"\n📊 OVERALL SUMMARY:")
        summary = data['summary']
        print(f"   Total Zones: {summary['total_zones']}")
        print(f"   Total Bins: {summary['total_bins']}")
        print(f"   Combined Distance: {summary['total_distance_km']} km")
        print(f"   Combined Time: {summary['total_duration_min']} minutes")
        
        print(f"\nZONE DETAILS:\n")
        for zone in data['zones']:
            print(f"{'─'*70}")
            print(f"📍 {zone['zone_name']}")
            print(f"   Depot: {zone['depot']['name']}")
            print(f"   Bins to collect: {zone['summary']['total_bins']}")
            print(f"   Route distance: {zone['summary']['total_distance_km']} km")
            print(f"   Driving time: {zone['summary']['driving_time_min']} min")
            print(f"   Service time: {zone['summary']['service_time_min']} min")
            print(f"   Total duration: {zone['summary']['estimated_duration_min']} min")
            print(f"   Average fill: {zone['summary']['average_fill_pct']}%")
            print(f"   Color: {zone['zone_color']}")
            
            # Show first 3 waypoints
            if zone['waypoints']:
                print(f"\n   Route (first 3 stops):")
                for i, wp in enumerate(zone['waypoints'][:3]):
                    if wp['type'] == 'depot':
                        print(f"      {i}. 🏢 {wp['location']}")
                    else:
                        print(f"      {i}. Bin {wp.get('bin_id', 'N/A')} - "
                              f"{wp.get('predicted_fill_level', 0)}% full")
                
                if len(zone['waypoints']) > 3:
                    print(f"      ... + {len(zone['waypoints']) - 3} more stops")
            print()
    else:
        print("No bins need collection at this time")

def test_single_vs_zone_comparison():
    """Test 3: Compare single route vs zone-based"""
    print_section("TEST 3: Single Route vs Zone-Based Comparison")
    
    target_time = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d-14-00')
    
    # Get single route
    single_response = requests.get(f"{BASE_URL}/api/route/{target_time}")
    single_data = single_response.json()
    
    # Get zone-based routes
    zone_response = requests.get(f"{BASE_URL}/api/route-by-zone/{target_time}")
    zone_data = zone_response.json()
    
    print("SINGLE ROUTE (One Truck):")
    print(f"  Bins: {single_data.get('bins_count', 0)}")
    print(f"  Distance: {single_data.get('total_distance_km', 0)} km")
    print(f"  Time: {single_data.get('estimated_time_hours', 0):.1f} hours")
    print(f"  Trucks needed: 1")
    
    print("\nZONE-BASED ROUTES (Multiple Trucks):")
    if 'summary' in zone_data:
        print(f"  Bins: {zone_data['summary']['total_bins']}")
        print(f"  Total Distance: {zone_data['summary']['total_distance_km']} km")
        print(f"  Time (parallel): {max([z['summary']['estimated_duration_min'] for z in zone_data['zones']])} min" if zone_data['zones'] else "0 min")
        print(f"  Trucks needed: {zone_data['summary']['total_zones']}")
        print(f"  Active Zones: {zone_data['summary']['total_zones']}")
    
    print("\nBENEFITS:")
    if zone_data.get('zones'):
        parallel_time = max([z['summary']['estimated_duration_min'] for z in zone_data['zones']])
        single_time = single_data.get('estimated_time_hours', 0) * 60
        
        if single_time > 0:
            time_savings = ((single_time - parallel_time) / single_time) * 100
            print(f"  - Time savings: {time_savings:.1f}% (with parallel operation)")
            print(f"  - Average distance per truck: {zone_data['summary']['total_distance_km'] / zone_data['summary']['total_zones']:.1f} km")
            print(f"  - Allows {zone_data['summary']['total_zones']} trucks to work simultaneously")

def main():
    print("\n" + "="*70)
    print("  CleanRoute Zone-Based Routing Test Suite")
    print("="*70)
    print(f"\nTesting against: {BASE_URL}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        if response.status_code != 200:
            print("ERROR: Server is not healthy!")
            return
        print("OK: Server is running\n")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Cannot connect to server: {e}")
        print("\nPlease start the server first:")
        print("  .\\quickstart.bat")
        return
    
    # Run tests
    tests = [
        ("Get Zones", test_get_zones),
        ("Zone-Based Routes", test_zone_routes),
        ("Single vs Zone Comparison", test_single_vs_zone_comparison),
    ]
    
    for name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\nERROR: Test '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    print_section("OK: All Tests Complete!")
    print("Next steps:")
    print("1. Open http://localhost:5001 to see the dashboard")
    print("2. Generate predictions for tomorrow")
    print("3. Use zone-based routing in your frontend")
    print()

if __name__ == "__main__":
    main()
