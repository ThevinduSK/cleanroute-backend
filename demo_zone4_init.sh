#!/bin/bash
# =============================================================================
# Initialize Zone 4 Bins as SLEEPING (Offline)
# =============================================================================
# Run this first to set up the demo scenario where all bins start sleeping

echo "Initializing Zone 4 bins (Nugegoda & Kotte) as SLEEPING..."
echo ""

# Add sleep_mode column if not exists and set all Zone 4 bins to sleep
PGPASSWORD=cleanroute_pass psql -h localhost -U cleanroute_user -d cleanroute_db << 'EOF'
-- Add sleep_mode column if not exists
ALTER TABLE bins ADD COLUMN IF NOT EXISTS sleep_mode BOOLEAN DEFAULT TRUE;

-- Insert Zone 4 bins (Nugegoda & Kotte) if they don't exist, or set to sleeping
INSERT INTO bins (bin_id, lat, lon, sleep_mode) VALUES
    ('COL401', 6.8550, 79.8800, TRUE),
    ('COL402', 6.8600, 79.8850, TRUE),
    ('COL403', 6.8680, 79.8920, TRUE),
    ('COL404', 6.8750, 79.8980, TRUE),
    ('COL405', 6.8850, 79.9050, TRUE),
    ('COL406', 6.8950, 79.8880, TRUE),
    ('COL407', 6.9050, 79.9100, TRUE),
    ('COL408', 6.9150, 79.9000, TRUE)
ON CONFLICT (bin_id) DO UPDATE SET sleep_mode = TRUE;

-- Show current status
SELECT bin_id, sleep_mode, last_seen 
FROM bins 
WHERE bin_id LIKE 'COL4%' 
ORDER BY bin_id;
EOF

echo ""
echo "Zone 4 bins initialized as SLEEPING (grey 💤 on map)"
echo ""
echo "Demo Flow:"
echo "   1. Open http://localhost:5001"
echo "   2. Login as admin"
echo "   3. Select Colombo → Nugegoda & Kotte"
echo "   4. Click 'Start Collection' → bins will show as waking"
echo "   5. Run ./demo_zone4_wake.sh to simulate devices responding"
echo "   6. Click 'Check Status' to see responses"
echo "   7. Click 'End Collection' → devices go back to sleep"
