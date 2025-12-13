#!/bin/bash
# =============================================================================
# Demo IoT Features - Heartbeat, ACK, Diagnostics, Firmware Status
# =============================================================================

CAFILE="/home/thevinduk/Repositories/cleanroute-backend/mqtt/certs/ca.crt"
HOST="localhost"
PORT="8883"

echo "IoT Features Demo"
echo "===================="
echo ""

# Pick a demo device
DEVICE="COL401"
PASSWORD="col_zone4_401"

echo "Using device: $DEVICE"
echo ""

# 1. Simulate Heartbeat
echo "[1]  Sending Heartbeat..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "$DEVICE" -P "$PASSWORD" \
  -t "cleanroute/bins/$DEVICE/heartbeat" \
  -m '{"rssi":-65,"uptime_seconds":3600,"free_memory_kb":128,"firmware_version":"1.2.3"}'
sleep 0.5
echo "   Heartbeat sent"
echo ""

# 2. Simulate Command ACK
echo "[2]  Sending Command Acknowledgment..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "$DEVICE" -P "$PASSWORD" \
  -t "cleanroute/bins/$DEVICE/ack" \
  -m '{"command_id":"test123","success":true}'
sleep 0.5
echo "   ACK sent"
echo ""

# 3. Simulate Diagnostic Response
echo "[3]  Sending Diagnostic Response..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "$DEVICE" -P "$PASSWORD" \
  -t "cleanroute/bins/$DEVICE/diagnostic" \
  -m '{
    "diagnostic_type":"full",
    "sensors":{
      "ultrasonic_cm":45.2,
      "temperature_c":31.5,
      "humidity_pct":68
    },
    "network":{
      "rssi":-62,
      "connection_type":"WiFi",
      "ip":"192.168.1.101"
    },
    "memory":{
      "free_kb":128,
      "total_kb":512,
      "heap_fragmentation_pct":12
    },
    "battery":{
      "voltage":3.85,
      "percentage":78,
      "charging":false
    },
    "firmware":{
      "version":"1.2.3",
      "build_date":"2025-12-01"
    }
  }'
sleep 0.5
echo "   Diagnostic sent"
echo ""

# 4. Simulate Firmware Update Progress
echo "[4]  Simulating Firmware Update Progress..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "$DEVICE" -P "$PASSWORD" \
  -t "cleanroute/bins/$DEVICE/firmware_status" \
  -m '{"status":"downloading","progress_pct":25}'
sleep 0.3

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "$DEVICE" -P "$PASSWORD" \
  -t "cleanroute/bins/$DEVICE/firmware_status" \
  -m '{"status":"downloading","progress_pct":50}'
sleep 0.3

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "$DEVICE" -P "$PASSWORD" \
  -t "cleanroute/bins/$DEVICE/firmware_status" \
  -m '{"status":"downloading","progress_pct":100}'
sleep 0.3

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "$DEVICE" -P "$PASSWORD" \
  -t "cleanroute/bins/$DEVICE/firmware_status" \
  -m '{"status":"installing","progress_pct":50}'
sleep 0.3

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "$DEVICE" -P "$PASSWORD" \
  -t "cleanroute/bins/$DEVICE/firmware_status" \
  -m '{"status":"completed","progress_pct":100}'
echo "   Firmware update simulation complete"
echo ""

# 5. Simulate Shadow State Update
echo "[5]  Sending Shadow State Update..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "$DEVICE" -P "$PASSWORD" \
  -t "cleanroute/bins/$DEVICE/shadow/reported" \
  -m '{
    "fill_pct":72,
    "batt_v":3.82,
    "temp_c":30.5,
    "firmware_version":"1.2.3",
    "config":{
      "telemetry_interval_minutes":60,
      "sleep_enabled":true
    }
  }'
sleep 0.5
echo "   Shadow state sent"
echo ""

echo "========================================"
echo "IoT Features Demo Complete!"
echo ""
echo "Check the backend logs to see:"
echo "   - Heartbeat received"
echo "   - Command ACK processed"
echo "   - Diagnostic stored"
echo "   - Firmware progress tracked"
echo "   - Shadow state updated"
echo ""
echo "🔗 API Endpoints to explore:"
echo "   GET  /api/iot/device/$DEVICE/heartbeats"
echo "   GET  /api/iot/device/$DEVICE/diagnostics"
echo "   GET  /api/iot/device/$DEVICE/power"
echo "   GET  /api/iot/device/$DEVICE/shadow"
echo "   GET  /api/iot/commands/pending"
echo "   GET  /api/iot/firmware/updates/pending"
