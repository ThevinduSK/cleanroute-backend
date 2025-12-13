#!/usr/bin/env python3
"""
Test script for CleanRoute IoT features.
Demonstrates device management, commands, and alerts.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_device_registration():
    """Test 1: Register a new device"""
    print_section("TEST 1: Device Registration")
    
    device_data = {
        "bin_id": "B002",
        "user_id": "USER001",
        "user_name": "Alice Johnson",
        "user_phone": "+94771234567",
        "wifi_ssid": "HomeWiFi",
        "lat": 6.9271,
        "lon": 79.8612
    }
    
    response = requests.post(f"{BASE_URL}/devices/register", json=device_data)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_user_devices():
    """Test 2: Get user's devices"""
    print_section("TEST 2: Get User Devices")
    
    response = requests.get(f"{BASE_URL}/devices/user/USER001")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_fleet_health():
    """Test 3: Check fleet health"""
    print_section("TEST 3: Fleet Health")
    
    response = requests.get(f"{BASE_URL}/fleet/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_wake_command():
    """Test 4: Send wake-up command"""
    print_section("TEST 4: Send Wake-Up Command")
    
    response = requests.post(f"{BASE_URL}/commands/B001/wake?collection_hours=12")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_collection_start():
    """Test 5: Start collection day"""
    print_section("TEST 5: Start Collection Day")
    
    response = requests.post(f"{BASE_URL}/collection/start?collection_hours=12")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_health_check():
    """Test 6: Run health checks"""
    print_section("TEST 6: Run Health Checks")
    
    response = requests.post(f"{BASE_URL}/monitoring/health-check")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_alerts():
    """Test 7: Get alerts"""
    print_section("TEST 7: Get Alerts")
    
    response = requests.get(f"{BASE_URL}/alerts")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_device_health():
    """Test 8: Get device health"""
    print_section("TEST 8: Device Health Status")
    
    response = requests.get(f"{BASE_URL}/devices/B001/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_command_history():
    """Test 9: Get command history"""
    print_section("TEST 9: Command History")
    
    response = requests.get(f"{BASE_URL}/commands/B001/history?limit=5")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def main():
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        CleanRoute IoT Backend - Feature Test Suite        ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"\nServer is running at {BASE_URL}")
    except requests.exceptions.RequestException:
        print(f"\nServer is not running at {BASE_URL}")
        print("Please start the server first:")
        print("  cd backend && source .venv/bin/activate")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return
    
    tests = [
        test_device_registration,
        test_user_devices,
        test_fleet_health,
        test_wake_command,
        test_device_health,
        test_command_history,
        test_health_check,
        test_alerts,
        test_collection_start,
    ]
    
    for test_func in tests:
        try:
            test_func()
            time.sleep(0.5)
        except Exception as e:
            print(f"Error: {e}")
    
    print_section("All Tests Complete!")
    print("Check the server logs to see MQTT commands being published.")
    print("\nNext steps:")
    print("1. Subscribe to MQTT commands:")
    print("   mosquitto_sub -h localhost -t 'cleanroute/bins/+/command' -v")
    print("2. Simulate device responses")
    print("3. View the web dashboard")

if __name__ == "__main__":
    main()
