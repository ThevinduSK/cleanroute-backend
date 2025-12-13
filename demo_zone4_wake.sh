#!/bin/bash
# =============================================================================
# Simulate Zone 4 Bins WAKING UP (Sending Telemetry)
# =============================================================================
# Run this AFTER clicking "Start Collection" in the UI
# Simulates devices receiving wake command and sending their status

CAFILE="/home/thevinduk/Repositories/cleanroute-backend/mqtt/certs/ca.crt"
HOST="localhost"
PORT="8883"

echo "Simulating Zone 4 devices WAKING UP..."
echo ""

# Zone 4: Nugegoda & Kotte (8 bins)
# These bins "wake up" and send their current fill status
echo "🔔 Devices receiving wake command and responding..."
sleep 1

# Simulate gradual response (like real devices)
echo "   COL401 responding..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL401" -P "col_zone4_401" \
  -t "cleanroute/bins/COL401/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL401","fill_pct":88.0,"batt_v":3.7,"temp_c":30.5,"lat":6.8550,"lon":79.8800}'
sleep 0.5

echo "   COL402 responding..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL402" -P "col_zone4_402" \
  -t "cleanroute/bins/COL402/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL402","fill_pct":41.0,"batt_v":4.0,"temp_c":29.5,"lat":6.8600,"lon":79.8850}'
sleep 0.5

echo "   COL403 responding..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL403" -P "col_zone4_403" \
  -t "cleanroute/bins/COL403/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL403","fill_pct":67.0,"batt_v":3.9,"temp_c":30.0,"lat":6.8680,"lon":79.8920}'
sleep 0.5

echo "   COL404 responding..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL404" -P "col_zone4_404" \
  -t "cleanroute/bins/COL404/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL404","fill_pct":93.0,"batt_v":3.6,"temp_c":31.5,"lat":6.8750,"lon":79.8980}'
sleep 0.5

echo "   COL405 responding..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL405" -P "col_zone4_405" \
  -t "cleanroute/bins/COL405/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL405","fill_pct":25.0,"batt_v":4.2,"temp_c":28.5,"lat":6.8850,"lon":79.9050}'
sleep 0.5

echo "   COL406 responding..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL406" -P "col_zone4_406" \
  -t "cleanroute/bins/COL406/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL406","fill_pct":72.0,"batt_v":3.9,"temp_c":30.0,"lat":6.8950,"lon":79.8880}'
sleep 0.5

echo "   COL407 responding..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL407" -P "col_zone4_407" \
  -t "cleanroute/bins/COL407/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL407","fill_pct":56.0,"batt_v":4.0,"temp_c":29.5,"lat":6.9050,"lon":79.9100}'
sleep 0.5

echo "   COL408 responding..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL408" -P "col_zone4_408" \
  -t "cleanroute/bins/COL408/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL408","fill_pct":84.0,"batt_v":3.8,"temp_c":30.5,"lat":6.9150,"lon":79.9000}'

echo ""
echo "All 8 Zone 4 devices have responded!"
echo ""
echo "Next Steps:"
echo "   1. Click 'Check Status' in the UI to see all bins reporting"
echo "   2. The bins should now appear as ACTIVE on the map"
echo "   3. Click 'Optimize Zone Route' to plan collection"
echo "   4. After collection, click 'Finish' then 'End Collection'"
