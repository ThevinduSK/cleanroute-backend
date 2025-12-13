#!/bin/bash
# =============================================================================
# Simulate Zone 4 Bins COLLECTED (Lower Fill Levels)
# =============================================================================
# Run this AFTER truck has "collected" to simulate post-collection status

CAFILE="/home/thevinduk/Repositories/cleanroute-backend/mqtt/certs/ca.crt"
HOST="localhost"
PORT="8883"

echo "🚛 Simulating Zone 4 devices after COLLECTION..."
echo ""

# After collection, bins should have low fill levels
echo "   COL401 - now empty..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL401" -P "col_zone4_401" \
  -t "cleanroute/bins/COL401/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL401","fill_pct":5.0,"batt_v":3.7,"temp_c":30.5,"lat":6.8550,"lon":79.8800,"emptied":true}'
sleep 0.3

echo "   COL402 - now empty..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL402" -P "col_zone4_402" \
  -t "cleanroute/bins/COL402/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL402","fill_pct":3.0,"batt_v":4.0,"temp_c":29.5,"lat":6.8600,"lon":79.8850,"emptied":true}'
sleep 0.3

echo "   COL403 - now empty..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL403" -P "col_zone4_403" \
  -t "cleanroute/bins/COL403/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL403","fill_pct":2.0,"batt_v":3.9,"temp_c":30.0,"lat":6.8680,"lon":79.8920,"emptied":true}'
sleep 0.3

echo "   COL404 - now empty..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL404" -P "col_zone4_404" \
  -t "cleanroute/bins/COL404/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL404","fill_pct":4.0,"batt_v":3.6,"temp_c":31.5,"lat":6.8750,"lon":79.8980,"emptied":true}'
sleep 0.3

echo "   COL405 - now empty..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL405" -P "col_zone4_405" \
  -t "cleanroute/bins/COL405/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL405","fill_pct":2.0,"batt_v":4.2,"temp_c":28.5,"lat":6.8850,"lon":79.9050,"emptied":true}'
sleep 0.3

echo "   COL406 - now empty..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL406" -P "col_zone4_406" \
  -t "cleanroute/bins/COL406/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL406","fill_pct":3.0,"batt_v":3.9,"temp_c":30.0,"lat":6.8950,"lon":79.8880,"emptied":true}'
sleep 0.3

echo "   COL407 - now empty..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL407" -P "col_zone4_407" \
  -t "cleanroute/bins/COL407/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL407","fill_pct":1.0,"batt_v":4.0,"temp_c":29.5,"lat":6.9050,"lon":79.9100,"emptied":true}'
sleep 0.3

echo "   COL408 - now empty..."
mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL408" -P "col_zone4_408" \
  -t "cleanroute/bins/COL408/telemetry" \
  -m '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","bin_id":"COL408","fill_pct":2.0,"batt_v":3.8,"temp_c":30.5,"lat":6.9150,"lon":79.9000,"emptied":true}'

echo ""
echo "All 8 Zone 4 bins now show as COLLECTED (low fill levels)"
echo ""
echo "Next Steps:"
echo "   1. Click 'Finish' in the UI to verify all bins collected"
echo "   2. All bins should show low fill (green)"
echo "   3. Click 'End Collection' to put devices to sleep"
