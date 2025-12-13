#!/bin/bash
# =============================================================================
# CleanRoute Demo - Colombo District (32 Bins across 4 Zones)
# =============================================================================
# Run this script to populate all Colombo bins with sample telemetry data
# Requires: MQTT broker running with TLS on port 8883

CAFILE="/home/thevinduk/Repositories/cleanroute-backend/mqtt/certs/ca.crt"
HOST="localhost"
PORT="8883"

echo "Publishing telemetry for 32 Colombo bins..."
echo ""

# =============================================================================
# ZONE 1: Fort & Pettah (8 bins) - Commercial area
# Bounds: lat 6.925-6.980, lon 79.840-79.865
# Depot: Fort Depot (6.9318, 79.8478)
# =============================================================================
echo "Zone 1: Fort & Pettah"

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL101" -P "col_zone1_101" \
  -t "cleanroute/bins/COL101/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL101","fill_pct":85.0,"batt_v":3.8,"temp_c":31.0,"lat":6.9350,"lon":79.8450}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL102" -P "col_zone1_102" \
  -t "cleanroute/bins/COL102/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL102","fill_pct":72.0,"batt_v":3.9,"temp_c":30.5,"lat":6.9380,"lon":79.8520}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL103" -P "col_zone1_103" \
  -t "cleanroute/bins/COL103/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL103","fill_pct":45.0,"batt_v":4.0,"temp_c":30.0,"lat":6.9420,"lon":79.8480}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL104" -P "col_zone1_104" \
  -t "cleanroute/bins/COL104/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL104","fill_pct":92.0,"batt_v":3.7,"temp_c":31.5,"lat":6.9500,"lon":79.8550}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL105" -P "col_zone1_105" \
  -t "cleanroute/bins/COL105/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL105","fill_pct":28.0,"batt_v":4.1,"temp_c":29.5,"lat":6.9550,"lon":79.8600}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL106" -P "col_zone1_106" \
  -t "cleanroute/bins/COL106/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL106","fill_pct":65.0,"batt_v":3.9,"temp_c":30.0,"lat":6.9600,"lon":79.8450}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL107" -P "col_zone1_107" \
  -t "cleanroute/bins/COL107/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL107","fill_pct":78.0,"batt_v":3.8,"temp_c":31.0,"lat":6.9700,"lon":79.8500}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL108" -P "col_zone1_108" \
  -t "cleanroute/bins/COL108/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL108","fill_pct":55.0,"batt_v":4.0,"temp_c":30.5,"lat":6.9750,"lon":79.8580}'

echo "  8 bins published"

# =============================================================================
# ZONE 2: Kollupitiya & Bambalapitiya (8 bins) - Central residential
# Bounds: lat 6.885-6.925, lon 79.845-79.865
# Depot: Galle Face Depot (6.9045, 79.8580)
# =============================================================================
echo "Zone 2: Kollupitiya & Bambalapitiya"

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL201" -P "col_zone2_201" \
  -t "cleanroute/bins/COL201/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL201","fill_pct":82.0,"batt_v":3.8,"temp_c":30.0,"lat":6.8900,"lon":79.8500}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL202" -P "col_zone2_202" \
  -t "cleanroute/bins/COL202/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL202","fill_pct":35.0,"batt_v":4.1,"temp_c":29.5,"lat":6.8950,"lon":79.8550}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL203" -P "col_zone2_203" \
  -t "cleanroute/bins/COL203/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL203","fill_pct":68.0,"batt_v":3.9,"temp_c":30.5,"lat":6.9000,"lon":79.8480}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL204" -P "col_zone2_204" \
  -t "cleanroute/bins/COL204/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL204","fill_pct":91.0,"batt_v":3.6,"temp_c":31.0,"lat":6.9050,"lon":79.8600}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL205" -P "col_zone2_205" \
  -t "cleanroute/bins/COL205/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL205","fill_pct":42.0,"batt_v":4.0,"temp_c":29.0,"lat":6.9100,"lon":79.8520}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL206" -P "col_zone2_206" \
  -t "cleanroute/bins/COL206/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL206","fill_pct":75.0,"batt_v":3.9,"temp_c":30.0,"lat":6.9150,"lon":79.8570}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL207" -P "col_zone2_207" \
  -t "cleanroute/bins/COL207/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL207","fill_pct":58.0,"batt_v":4.0,"temp_c":30.5,"lat":6.9200,"lon":79.8500}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL208" -P "col_zone2_208" \
  -t "cleanroute/bins/COL208/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL208","fill_pct":88.0,"batt_v":3.7,"temp_c":31.0,"lat":6.9230,"lon":79.8620}'

echo "  8 bins published"

# =============================================================================
# ZONE 3: Wellawatta & Dehiwala (8 bins) - South residential
# Bounds: lat 6.830-6.885, lon 79.850-79.875
# Depot: Dehiwala Depot (6.8568, 79.8610)
# =============================================================================
echo "Zone 3: Wellawatta & Dehiwala"

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL301" -P "col_zone3_301" \
  -t "cleanroute/bins/COL301/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL301","fill_pct":77.0,"batt_v":3.9,"temp_c":30.0,"lat":6.8350,"lon":79.8550}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL302" -P "col_zone3_302" \
  -t "cleanroute/bins/COL302/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL302","fill_pct":22.0,"batt_v":4.2,"temp_c":29.0,"lat":6.8400,"lon":79.8600}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL303" -P "col_zone3_303" \
  -t "cleanroute/bins/COL303/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL303","fill_pct":63.0,"batt_v":3.9,"temp_c":30.5,"lat":6.8450,"lon":79.8650}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL304" -P "col_zone3_304" \
  -t "cleanroute/bins/COL304/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL304","fill_pct":95.0,"batt_v":3.5,"temp_c":32.0,"lat":6.8500,"lon":79.8700}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL305" -P "col_zone3_305" \
  -t "cleanroute/bins/COL305/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL305","fill_pct":48.0,"batt_v":4.0,"temp_c":29.5,"lat":6.8600,"lon":79.8580}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL306" -P "col_zone3_306" \
  -t "cleanroute/bins/COL306/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL306","fill_pct":81.0,"batt_v":3.8,"temp_c":30.5,"lat":6.8650,"lon":79.8520}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL307" -P "col_zone3_307" \
  -t "cleanroute/bins/COL307/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL307","fill_pct":33.0,"batt_v":4.1,"temp_c":29.0,"lat":6.8750,"lon":79.8600}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL308" -P "col_zone3_308" \
  -t "cleanroute/bins/COL308/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL308","fill_pct":70.0,"batt_v":3.9,"temp_c":30.0,"lat":6.8800,"lon":79.8680}'

echo "  8 bins published"

# =============================================================================
# ZONE 4: Nugegoda & Kotte (8 bins) - Suburban east
# Bounds: lat 6.850-6.920, lon 79.875-79.920
# Depot: Nugegoda Depot (6.8654, 79.8896)
# =============================================================================
echo "Zone 4: Nugegoda & Kotte"

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL401" -P "col_zone4_401" \
  -t "cleanroute/bins/COL401/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL401","fill_pct":88.0,"batt_v":3.7,"temp_c":30.5,"lat":6.8550,"lon":79.8800}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL402" -P "col_zone4_402" \
  -t "cleanroute/bins/COL402/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL402","fill_pct":41.0,"batt_v":4.0,"temp_c":29.5,"lat":6.8600,"lon":79.8850}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL403" -P "col_zone4_403" \
  -t "cleanroute/bins/COL403/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL403","fill_pct":67.0,"batt_v":3.9,"temp_c":30.0,"lat":6.8680,"lon":79.8920}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL404" -P "col_zone4_404" \
  -t "cleanroute/bins/COL404/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL404","fill_pct":93.0,"batt_v":3.6,"temp_c":31.5,"lat":6.8750,"lon":79.8980}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL405" -P "col_zone4_405" \
  -t "cleanroute/bins/COL405/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL405","fill_pct":25.0,"batt_v":4.2,"temp_c":28.5,"lat":6.8850,"lon":79.9050}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL406" -P "col_zone4_406" \
  -t "cleanroute/bins/COL406/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL406","fill_pct":72.0,"batt_v":3.9,"temp_c":30.0,"lat":6.8950,"lon":79.8880}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL407" -P "col_zone4_407" \
  -t "cleanroute/bins/COL407/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL407","fill_pct":56.0,"batt_v":4.0,"temp_c":29.5,"lat":6.9050,"lon":79.9100}'

mosquitto_pub -h $HOST -p $PORT --cafile $CAFILE -u "COL408" -P "col_zone4_408" \
  -t "cleanroute/bins/COL408/telemetry" \
  -m '{"ts":"2025-12-13T10:00:00Z","bin_id":"COL408","fill_pct":84.0,"batt_v":3.8,"temp_c":30.5,"lat":6.9150,"lon":79.9000}'

echo "  8 bins published"

echo ""
echo "========================================="
echo "All 32 Colombo bins published!"
echo "========================================="
echo ""
echo "Zone Summary:"
echo "  Zone 1 (Fort & Pettah):        COL101-COL108"
echo "  Zone 2 (Kollupitiya):          COL201-COL208"
echo "  Zone 3 (Wellawatta/Dehiwala):  COL301-COL308"
echo "  Zone 4 (Nugegoda/Kotte):       COL401-COL408"
echo ""
echo "View at: http://localhost:5001"
