#!/usr/bin/env python3
"""
Test script for ML Prediction and Route Optimization features.
Tests EWMA-based forecasting and greedy nearest-neighbor routing.
"""
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_json(data):
    print(json.dumps(data, indent=2))

# ─────────────────────────────────────────────────────────────────────────────
# Test ML Prediction Endpoints
# ─────────────────────────────────────────────────────────────────────────────

def test_forecast_bins():
    """Test 1: Forecast all bins for tomorrow afternoon"""
    print_section("TEST 1: Forecast Bins - Tomorrow Afternoon")
    
    response = requests.get(
        f"{BASE_URL}/bins/forecast",
        params={
            "target_time": "tomorrow_afternoon",
            "threshold": 80
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    print(f"\nTarget Time: {data.get('target_time')}")
    print(f"Threshold: {data.get('threshold_pct')}%")
    print(f"Total Bins: {data.get('total_bins')}")
    print(f"Bins Needing Collection: {data.get('bins_needing_collection')}")
    
    # Show first 3 predictions
    if data.get('predictions'):
        print("\nSample Predictions:")
        for pred in data['predictions'][:3]:
            print(f"  • {pred['bin_id']}: {pred['current_fill']}% → {pred['predicted_fill']}% "
                  f"({pred['confidence']} confidence)")


def test_forecast_bins_custom_time():
    """Test 2: Forecast with custom time (24 hours)"""
    print_section("TEST 2: Forecast Bins - In 24 Hours")
    
    response = requests.get(
        f"{BASE_URL}/bins/forecast",
        params={
            "target_time": "24h",
            "threshold": 85
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    print(f"Bins needing collection (≥85%): {data.get('bins_needing_collection')}")


def test_single_bin_prediction():
    """Test 3: Get prediction for single bin"""
    print_section("TEST 3: Single Bin Prediction")
    
    # First get a bin ID
    bins_response = requests.get(f"{BASE_URL}/bins/latest")
    bins = bins_response.json()
    
    if bins:
        bin_id = bins[0]['bin_id']
        
        response = requests.get(
            f"{BASE_URL}/bins/{bin_id}/prediction",
            params={"target_time": "tomorrow_afternoon"}
        )
        
        print(f"Status: {response.status_code}")
        print_json(response.json())


def test_bins_at_risk():
    """Test 4: Get bins at risk (legacy endpoint)"""
    print_section("TEST 4: Bins At Risk - 48 Hours")
    
    response = requests.get(
        f"{BASE_URL}/bins/at_risk",
        params={"threshold_hours": 48}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    print(f"Bins at risk: {data.get('count')}")
    if data.get('bins_at_risk'):
        print("\nTop 3 at-risk bins:")
        for bin_data in data['bins_at_risk'][:3]:
            print(f"  • {bin_data['bin_id']}: {bin_data['predicted_fill']}%")


# ─────────────────────────────────────────────────────────────────────────────
# Test Route Optimization
# ─────────────────────────────────────────────────────────────────────────────

def test_route_optimization():
    """Test 5: Generate optimal route"""
    print_section("TEST 5: Route Optimization - Tomorrow Afternoon")
    
    request_body = {
        "target_time": "tomorrow_afternoon",
        "threshold_pct": 80,
        "depot_location": {
            "lat": 6.9271,
            "lon": 79.8612,
            "name": "Municipal Office"
        },
        "algorithm": "greedy"
    }
    
    response = requests.post(
        f"{BASE_URL}/routes/optimize",
        json=request_body
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    if data.get('route'):
        route = data['route']
        summary = route['summary']
        
        print(f"\n📊 Route Summary:")
        print(f"  • Total Bins: {summary['total_bins']}")
        print(f"  • Total Distance: {summary['total_distance_km']} km")
        print(f"  • Driving Time: {summary['driving_time_min']} minutes")
        print(f"  • Service Time: {summary['service_time_min']} minutes")
        print(f"  • Total Duration: {summary['estimated_duration_min']} minutes")
        print(f"  • Average Fill: {summary['average_fill_pct']}%")
        
        print(f"\nRoute Details (first 5 stops):")
        for waypoint in route['waypoints'][:5]:
            if waypoint['type'] == 'depot':
                print(f"  {waypoint['order']}. 📍 {waypoint['name']}")
            else:
                print(f"  {waypoint['order']}. Bin {waypoint['bin_id']} "
                      f"({waypoint['predicted_fill']}%) - "
                      f"{waypoint['distance_from_prev_km']} km from previous")
        
        if len(route['waypoints']) > 5:
            print(f"  ... ({len(route['waypoints']) - 5} more stops)")
    else:
        print("No route generated (no bins need collection)")


def test_route_with_different_threshold():
    """Test 6: Route with 70% threshold (more bins)"""
    print_section("TEST 6: Route Optimization - 70% Threshold")
    
    request_body = {
        "target_time": "tomorrow_afternoon",
        "threshold_pct": 70,
        "algorithm": "greedy"
    }
    
    response = requests.post(
        f"{BASE_URL}/routes/optimize",
        json=request_body
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    if data.get('route'):
        summary = data['route']['summary']
        print(f"With 70% threshold:")
        print(f"  • Bins to collect: {summary['total_bins']}")
        print(f"  • Total distance: {summary['total_distance_km']} km")
        print(f"  • Duration: {summary['estimated_duration_min']} minutes")


def test_route_custom_depot():
    """Test 7: Route with custom depot location"""
    print_section("TEST 7: Route with Custom Start Point")
    
    request_body = {
        "target_time": "6h",
        "threshold_pct": 80,
        "depot_location": {
            "lat": 6.9102,
            "lon": 79.8623,
            "name": "Alternative Depot"
        },
        "algorithm": "greedy"
    }
    
    response = requests.post(
        f"{BASE_URL}/routes/optimize",
        json=request_body
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    if data.get('route'):
        print(f"Starting from: {data['depot']['name']}")
        print(f"Total distance: {data['route']['summary']['total_distance_km']} km")


# ─────────────────────────────────────────────────────────────────────────────
# Comparison Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_compare_time_scenarios():
    """Test 8: Compare different collection times"""
    print_section("TEST 8: Compare Collection Time Scenarios")
    
    scenarios = [
        ("6 hours", "6h"),
        ("Tomorrow morning", "tomorrow_morning"),
        ("Tomorrow afternoon", "tomorrow_afternoon"),
        ("48 hours", "48h")
    ]
    
    print("Scenario Comparison:")
    print("-" * 70)
    
    for name, preset in scenarios:
        response = requests.get(
            f"{BASE_URL}/bins/forecast",
            params={"target_time": preset, "threshold": 80}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"{name:20} → {data['bins_needing_collection']:2} bins need collection")


# ─────────────────────────────────────────────────────────────────────────────
# Main Test Runner
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*70)
    print("  CleanRoute ML & Route Optimization Test Suite")
    print("="*70)
    print("\nTesting against: " + BASE_URL)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("Server is not healthy!")
            return
        print("Server is running\n")
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Cannot connect to server: {e}")
        print("\nPlease start the server first:")
        print("  cd backend")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return
    
    # Run tests
    tests = [
        ("Forecast Bins", test_forecast_bins),
        ("Forecast Custom Time", test_forecast_bins_custom_time),
        ("Single Bin Prediction", test_single_bin_prediction),
        ("Bins At Risk", test_bins_at_risk),
        ("Route Optimization", test_route_optimization),
        ("Route Different Threshold", test_route_with_different_threshold),
        ("Route Custom Depot", test_route_custom_depot),
        ("Compare Scenarios", test_compare_time_scenarios),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            time.sleep(0.5)  # Small delay between tests
        except Exception as e:
            print(f"\n[FAIL] Test failed: {e}")
            failed += 1
    
    # Summary
    print_section("Test Summary")
    print(f"[PASS] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\nAll tests passed!")
    
    print("\n" + "="*70)
    print("  Next Steps:")
    print("="*70)
    print("1. Build frontend UI to visualize routes on map")
    print("2. Add route export (PDF, GPX)")
    print("3. Implement real-time route updates")
    print("4. Consider upgrading to OR-Tools TSP solver for optimal routes")
    print()


if __name__ == "__main__":
    main()
