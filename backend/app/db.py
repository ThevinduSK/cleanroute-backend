"""
Database connection helper for PostgreSQL.
Provides connection pooling and helper functions.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from . import config

# ─────────────────────────────────────────────────────────────────────────────
# Connection Helper
# ─────────────────────────────────────────────────────────────────────────────

def get_connection():
    """Get a new database connection."""
    return psycopg2.connect(config.DATABASE_URL)


@contextmanager
def get_cursor(commit=False):
    """
    Context manager for database cursor.
    Automatically handles connection and cursor cleanup.
    
    Usage:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM bins")
            rows = cur.fetchall()
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────

def check_db_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1")
            return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Bin Operations
# ─────────────────────────────────────────────────────────────────────────────

def upsert_bin(bin_id: str, lat: float, lon: float, last_seen: str):
    """
    Insert or update a bin record.
    Updates last_seen timestamp on every telemetry message.
    When telemetry is received, the device is awake (sleep_mode = FALSE).
    """
    sql = """
        INSERT INTO bins (bin_id, lat, lon, last_seen, sleep_mode)
        VALUES (%s, %s, %s, %s, FALSE)
        ON CONFLICT (bin_id) DO UPDATE SET
            lat = EXCLUDED.lat,
            lon = EXCLUDED.lon,
            last_seen = EXCLUDED.last_seen,
            sleep_mode = FALSE
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id, lat, lon, last_seen))


def update_bin_emptied(bin_id: str, emptied_at: str):
    """Update the last_emptied timestamp when a bin is emptied."""
    sql = """
        UPDATE bins SET last_emptied = %s WHERE bin_id = %s
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (emptied_at, bin_id))


def get_all_bins_latest():
    """
    Get all bins with their latest telemetry data.
    Returns one row per bin with the most recent fill percentage.
    Bins in sleep mode are marked as offline.
    """
    sql = """
        SELECT DISTINCT ON (b.bin_id)
            b.bin_id,
            b.lat,
            b.lon,
            b.last_seen,
            b.last_emptied,
            b.sleep_mode,
            t.fill_pct,
            t.batt_v,
            t.temp_c,
            t.ts as last_telemetry_ts
        FROM bins b
        LEFT JOIN telemetry t ON b.bin_id = t.bin_id
        ORDER BY b.bin_id, t.ts DESC
    """
    with get_cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


def ensure_sleep_mode_column():
    """Ensure the bins table has the sleep_mode column."""
    sql = """
        ALTER TABLE bins ADD COLUMN IF NOT EXISTS sleep_mode BOOLEAN DEFAULT TRUE
    """
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(sql)
    except Exception:
        pass  # Column might already exist


def set_bin_sleep_mode(bin_id: str, sleep_mode: bool):
    """Set the sleep mode for a specific bin."""
    ensure_sleep_mode_column()
    sql = """
        UPDATE bins SET sleep_mode = %s WHERE bin_id = %s
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (sleep_mode, bin_id))


def set_zone_sleep_mode(bin_ids: list, sleep_mode: bool):
    """Set the sleep mode for multiple bins."""
    ensure_sleep_mode_column()
    if not bin_ids:
        return
    sql = """
        UPDATE bins SET sleep_mode = %s WHERE bin_id = ANY(%s)
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (sleep_mode, bin_ids))


# ─────────────────────────────────────────────────────────────────────────────
# Telemetry Operations
# ─────────────────────────────────────────────────────────────────────────────

def insert_telemetry(
    ts: str,
    bin_id: str,
    fill_pct: float,
    batt_v: float = None,
    temp_c: float = None,
    emptied: bool = False,
    lat: float = None,
    lon: float = None
):
    """Insert a new telemetry record."""
    sql = """
        INSERT INTO telemetry (ts, bin_id, fill_pct, batt_v, temp_c, emptied, lat, lon)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (ts, bin_id, fill_pct, batt_v, temp_c, emptied, lat, lon))


def get_recent_telemetry(bin_id: str, limit: int = 100):
    """Get the most recent telemetry records for a specific bin."""
    sql = """
        SELECT id, ts, bin_id, fill_pct, batt_v, temp_c, emptied, lat, lon, received_at
        FROM telemetry
        WHERE bin_id = %s
        ORDER BY ts DESC
        LIMIT %s
    """
    with get_cursor() as cur:
        cur.execute(sql, (bin_id, limit))
        return cur.fetchall()


def get_all_recent_telemetry(limit: int = 500):
    """Get the most recent telemetry records across all bins."""
    sql = """
        SELECT id, ts, bin_id, fill_pct, batt_v, temp_c, emptied, lat, lon, received_at
        FROM telemetry
        ORDER BY ts DESC
        LIMIT %s
    """
    with get_cursor() as cur:
        cur.execute(sql, (limit,))
        return cur.fetchall()


# ─────────────────────────────────────────────────────────────────────────────
# Device Management Operations
# ─────────────────────────────────────────────────────────────────────────────

def register_device(
    bin_id: str,
    user_id: str,
    user_name: str,
    user_phone: str,
    wifi_ssid: str,
    lat: float = None,
    lon: float = None
):
    """Register a new device with user information."""
    sql = """
        INSERT INTO bins (bin_id, user_id, user_name, user_phone, wifi_ssid, lat, lon, registered_at, device_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 'offline')
        ON CONFLICT (bin_id) DO UPDATE SET
            user_id = EXCLUDED.user_id,
            user_name = EXCLUDED.user_name,
            user_phone = EXCLUDED.user_phone,
            wifi_ssid = EXCLUDED.wifi_ssid,
            lat = EXCLUDED.lat,
            lon = EXCLUDED.lon,
            registered_at = NOW()
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id, user_id, user_name, user_phone, wifi_ssid, lat, lon))


def update_device_status(bin_id: str, status: str):
    """Update device online/offline status."""
    sql = "UPDATE bins SET device_status = %s WHERE bin_id = %s"
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (status, bin_id))


def get_user_bins(user_id: str):
    """Get all bins registered to a user."""
    sql = """
        SELECT bin_id, lat, lon, last_seen, device_status, sleep_mode, registered_at
        FROM bins
        WHERE user_id = %s
    """
    with get_cursor() as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchall()


# ─────────────────────────────────────────────────────────────────────────────
# Alerts Operations
# ─────────────────────────────────────────────────────────────────────────────

def create_alert(bin_id: str, alert_type: str, severity: str, message: str) -> int:
    """Create a new alert."""
    sql = """
        INSERT INTO alerts (bin_id, alert_type, severity, message)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id, alert_type, severity, message))
        return cur.fetchone()['id']


def get_unresolved_alerts(bin_id: str = None):
    """Get unresolved alerts, optionally filtered by bin_id."""
    if bin_id:
        sql = """
            SELECT id, bin_id, alert_type, severity, message, created_at
            FROM alerts
            WHERE bin_id = %s AND resolved = FALSE
            ORDER BY created_at DESC
        """
        with get_cursor() as cur:
            cur.execute(sql, (bin_id,))
            return cur.fetchall()
    else:
        sql = """
            SELECT id, bin_id, alert_type, severity, message, created_at
            FROM alerts
            WHERE resolved = FALSE
            ORDER BY created_at DESC
        """
        with get_cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()


def resolve_alert(alert_id: int):
    """Mark an alert as resolved."""
    sql = "UPDATE alerts SET resolved = TRUE, resolved_at = NOW() WHERE id = %s"
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (alert_id,))


# ─────────────────────────────────────────────────────────────────────────────
# Commands Log Operations
# ─────────────────────────────────────────────────────────────────────────────

def log_command(bin_id: str, command_type: str, payload: dict):
    """Log a command sent to a device."""
    sql = """
        INSERT INTO commands_log (bin_id, command_type, payload)
        VALUES (%s, %s, %s)
    """
    import json
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id, command_type, json.dumps(payload)))


def get_command_history(bin_id: str, limit: int = 50):
    """Get command history for a bin."""
    sql = """
        SELECT id, command_type, payload, sent_at, acknowledged, ack_at
        FROM commands_log
        WHERE bin_id = %s
        ORDER BY sent_at DESC
        LIMIT %s
    """
    with get_cursor() as cur:
        cur.execute(sql, (bin_id, limit))
        return cur.fetchall()


# ─────────────────────────────────────────────────────────────────────────────
# Bin Management (Admin)
# ─────────────────────────────────────────────────────────────────────────────

def delete_bin(bin_id: str) -> bool:
    """
    Delete a bin and all its associated data.
    Returns True if bin was deleted, False if not found.
    """
    # First delete related records
    sql_telemetry = "DELETE FROM telemetry WHERE bin_id = %s"
    sql_alerts = "DELETE FROM alerts WHERE bin_id = %s"
    sql_commands = "DELETE FROM commands_log WHERE bin_id = %s"
    sql_bin = "DELETE FROM bins WHERE bin_id = %s RETURNING bin_id"
    
    with get_cursor(commit=True) as cur:
        cur.execute(sql_telemetry, (bin_id,))
        cur.execute(sql_alerts, (bin_id,))
        cur.execute(sql_commands, (bin_id,))
        cur.execute(sql_bin, (bin_id,))
        result = cur.fetchone()
        return result is not None


def get_bin_by_id(bin_id: str):
    """Get a specific bin by ID."""
    sql = """
        SELECT bin_id, lat, lon, last_seen, last_emptied, device_status,
               user_id, user_name, registered_at
        FROM bins
        WHERE bin_id = %s
    """
    with get_cursor() as cur:
        cur.execute(sql, (bin_id,))
        return cur.fetchone()


def get_all_bins():
    """Get all bins (basic info only)."""
    sql = """
        SELECT bin_id, lat, lon, last_seen, device_status
        FROM bins
        ORDER BY bin_id
    """
    with get_cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


# ─────────────────────────────────────────────────────────────────────────────
# Admin Authentication
# ─────────────────────────────────────────────────────────────────────────────

def init_admin_table():
    """Create admin users table if not exists."""
    sql = """
        CREATE TABLE IF NOT EXISTS admin_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            last_login TIMESTAMP
        )
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql)


def create_admin_user(username: str, password_hash: str) -> bool:
    """Create a new admin user."""
    sql = """
        INSERT INTO admin_users (username, password_hash)
        VALUES (%s, %s)
        ON CONFLICT (username) DO NOTHING
        RETURNING id
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (username, password_hash))
        result = cur.fetchone()
        return result is not None


def get_admin_by_username(username: str):
    """Get admin user by username."""
    sql = """
        SELECT id, username, password_hash, created_at, last_login
        FROM admin_users
        WHERE username = %s
    """
    with get_cursor() as cur:
        cur.execute(sql, (username,))
        return cur.fetchone()


def update_admin_last_login(username: str):
    """Update admin's last login timestamp."""
    sql = """
        UPDATE admin_users
        SET last_login = NOW()
        WHERE username = %s
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (username,))


# ─────────────────────────────────────────────────────────────────────────────
# Collection Sessions
# ─────────────────────────────────────────────────────────────────────────────

def init_collection_sessions_table():
    """Initialize the collection_sessions table."""
    sql = """
        CREATE TABLE IF NOT EXISTS collection_sessions (
            id SERIAL PRIMARY KEY,
            zone_id VARCHAR(100) NOT NULL,
            zone_name VARCHAR(200),
            status VARCHAR(50) NOT NULL DEFAULT 'started',
            started_at TIMESTAMP DEFAULT NOW(),
            checked_at TIMESTAMP,
            finished_at TIMESTAMP,
            ended_at TIMESTAMP,
            bins_total INT DEFAULT 0,
            bins_responded INT DEFAULT 0,
            bins_collected INT DEFAULT 0,
            admin_user VARCHAR(100)
        )
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql)


def start_collection_session(zone_id: str, zone_name: str, bins_total: int, admin_user: str = None) -> int:
    """
    Start a new collection session for a zone.
    
    Returns:
        Session ID
    """
    # First, make sure the table exists
    init_collection_sessions_table()
    
    sql = """
        INSERT INTO collection_sessions (zone_id, zone_name, status, bins_total, admin_user)
        VALUES (%s, %s, 'started', %s, %s)
        RETURNING id
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (zone_id, zone_name, bins_total, admin_user))
        result = cur.fetchone()
        return result['id'] if result else None


def update_collection_session_status(session_id: int, status: str, **kwargs):
    """
    Update collection session status.
    
    Args:
        session_id: Session ID
        status: New status ('started', 'checked', 'finished', 'ended')
        **kwargs: Additional fields to update (bins_responded, bins_collected, etc.)
    """
    updates = ["status = %s"]
    params = [status]
    
    # Add timestamp based on status
    if status == 'checked':
        updates.append("checked_at = NOW()")
    elif status == 'finished':
        updates.append("finished_at = NOW()")
    elif status == 'ended':
        updates.append("ended_at = NOW()")
    
    # Add additional fields
    for key, value in kwargs.items():
        if key in ['bins_responded', 'bins_collected']:
            updates.append(f"{key} = %s")
            params.append(value)
    
    params.append(session_id)
    
    sql = f"UPDATE collection_sessions SET {', '.join(updates)} WHERE id = %s"
    with get_cursor(commit=True) as cur:
        cur.execute(sql, params)


def get_collection_session(session_id: int):
    """Get collection session by ID."""
    sql = "SELECT * FROM collection_sessions WHERE id = %s"
    with get_cursor() as cur:
        cur.execute(sql, (session_id,))
        return cur.fetchone()


def get_active_collection_session(zone_id: str):
    """Get active (not ended) collection session for a zone."""
    sql = """
        SELECT * FROM collection_sessions 
        WHERE zone_id = %s AND status != 'ended'
        ORDER BY started_at DESC
        LIMIT 1
    """
    with get_cursor() as cur:
        cur.execute(sql, (zone_id,))
        return cur.fetchone()


def get_zone_bins_status(zone_id: str) -> dict:
    """
    Get status of bins in a zone for collection tracking.
    
    Returns:
        Dictionary with bins info including which have responded recently
    """
    from . import mqtt_commands
    
    bins = mqtt_commands.get_bins_in_zone(zone_id)
    
    if not bins:
        return {
            "total": 0,
            "responded": 0,
            "pending": 0,
            "bins": []
        }
    
    # Get bins that have reported in the last 2 hours
    sql = """
        SELECT b.bin_id, b.last_seen, b.sleep_mode, t.fill_pct
        FROM bins b
        LEFT JOIN (
            SELECT DISTINCT ON (bin_id) bin_id, fill_pct
            FROM telemetry
            ORDER BY bin_id, ts DESC
        ) t ON b.bin_id = t.bin_id
        WHERE b.bin_id = ANY(%s)
    """
    
    with get_cursor() as cur:
        cur.execute(sql, (bins,))
        rows = cur.fetchall()
    
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(hours=2)
    
    responded = 0
    bins_status = []
    
    for row in rows:
        last_seen = row['last_seen']
        # Make timezone-aware comparison
        if last_seen and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        is_recent = last_seen and last_seen > threshold
        if is_recent:
            responded += 1
        
        bins_status.append({
            "bin_id": row['bin_id'],
            "last_seen": row['last_seen'].isoformat() if row['last_seen'] else None,
            "fill_pct": float(row['fill_pct']) if row['fill_pct'] else None,
            "sleep_mode": row['sleep_mode'],
            "responded": is_recent
        })
    
    return {
        "total": len(bins),
        "responded": responded,
        "pending": len(bins) - responded,
        "bins": bins_status
    }


# ─────────────────────────────────────────────────────────────────────────────
# Device Heartbeat System
# ─────────────────────────────────────────────────────────────────────────────

def init_heartbeat_table():
    """Initialize the device_heartbeats table."""
    sql = """
        CREATE TABLE IF NOT EXISTS device_heartbeats (
            id SERIAL PRIMARY KEY,
            bin_id VARCHAR(50) NOT NULL REFERENCES bins(bin_id) ON DELETE CASCADE,
            received_at TIMESTAMP DEFAULT NOW(),
            rssi INT,
            uptime_seconds INT,
            free_memory_kb INT,
            firmware_version VARCHAR(50)
        );
        CREATE INDEX IF NOT EXISTS idx_heartbeats_bin_id ON device_heartbeats(bin_id);
        CREATE INDEX IF NOT EXISTS idx_heartbeats_received_at ON device_heartbeats(received_at);
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql)


def record_heartbeat(bin_id: str, rssi: int = None, uptime_seconds: int = None, 
                     free_memory_kb: int = None, firmware_version: str = None):
    """Record a device heartbeat."""
    sql = """
        INSERT INTO device_heartbeats (bin_id, rssi, uptime_seconds, free_memory_kb, firmware_version)
        VALUES (%s, %s, %s, %s, %s)
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id, rssi, uptime_seconds, free_memory_kb, firmware_version))
    
    # Update bin's last_seen and device_status
    update_sql = "UPDATE bins SET last_seen = NOW(), device_status = 'online' WHERE bin_id = %s"
    with get_cursor(commit=True) as cur:
        cur.execute(update_sql, (bin_id,))


def get_devices_needing_heartbeat(timeout_minutes: int = 5) -> list:
    """Get devices that haven't sent a heartbeat recently."""
    from datetime import datetime, timedelta, timezone
    threshold = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
    
    sql = """
        SELECT bin_id, last_seen, device_status, sleep_mode
        FROM bins
        WHERE sleep_mode = FALSE
        AND (last_seen < %s OR last_seen IS NULL)
        AND device_status != 'offline'
    """
    with get_cursor() as cur:
        cur.execute(sql, (threshold,))
        return cur.fetchall()


def get_device_heartbeat_history(bin_id: str, limit: int = 100) -> list:
    """Get heartbeat history for a device."""
    sql = """
        SELECT received_at, rssi, uptime_seconds, free_memory_kb, firmware_version
        FROM device_heartbeats
        WHERE bin_id = %s
        ORDER BY received_at DESC
        LIMIT %s
    """
    with get_cursor() as cur:
        cur.execute(sql, (bin_id, limit))
        return cur.fetchall()


# ─────────────────────────────────────────────────────────────────────────────
# Command ACK/Retry System
# ─────────────────────────────────────────────────────────────────────────────

def init_command_ack_table():
    """Initialize the command_acknowledgments table."""
    sql = """
        CREATE TABLE IF NOT EXISTS command_acknowledgments (
            id SERIAL PRIMARY KEY,
            command_id VARCHAR(100) UNIQUE NOT NULL,
            bin_id VARCHAR(50) NOT NULL,
            command_type VARCHAR(50) NOT NULL,
            payload JSONB,
            sent_at TIMESTAMP DEFAULT NOW(),
            ack_received_at TIMESTAMP,
            retry_count INT DEFAULT 0,
            max_retries INT DEFAULT 3,
            status VARCHAR(20) DEFAULT 'pending',
            error_message TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_cmd_ack_bin_id ON command_acknowledgments(bin_id);
        CREATE INDEX IF NOT EXISTS idx_cmd_ack_status ON command_acknowledgments(status);
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql)


def create_pending_command(command_id: str, bin_id: str, command_type: str, payload: dict = None) -> int:
    """Create a pending command that expects acknowledgment."""
    import json
    sql = """
        INSERT INTO command_acknowledgments (command_id, bin_id, command_type, payload)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (command_id, bin_id, command_type, json.dumps(payload) if payload else None))
        result = cur.fetchone()
        return result['id'] if result else None


def acknowledge_command(command_id: str, success: bool = True, error_message: str = None):
    """Mark a command as acknowledged."""
    status = 'acknowledged' if success else 'failed'
    sql = """
        UPDATE command_acknowledgments
        SET ack_received_at = NOW(), status = %s, error_message = %s
        WHERE command_id = %s
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (status, error_message, command_id))


def get_pending_commands(bin_id: str = None, older_than_seconds: int = 30) -> list:
    """Get commands pending acknowledgment."""
    from datetime import datetime, timedelta, timezone
    threshold = datetime.now(timezone.utc) - timedelta(seconds=older_than_seconds)
    
    if bin_id:
        sql = """
            SELECT * FROM command_acknowledgments
            WHERE bin_id = %s AND status = 'pending' AND sent_at < %s AND retry_count < max_retries
        """
        params = (bin_id, threshold)
    else:
        sql = """
            SELECT * FROM command_acknowledgments
            WHERE status = 'pending' AND sent_at < %s AND retry_count < max_retries
        """
        params = (threshold,)
    
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def increment_command_retry(command_id: str):
    """Increment retry count for a command."""
    sql = """
        UPDATE command_acknowledgments
        SET retry_count = retry_count + 1, sent_at = NOW()
        WHERE command_id = %s
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (command_id,))


def mark_command_failed(command_id: str, error_message: str = "Max retries exceeded"):
    """Mark a command as failed after max retries."""
    sql = """
        UPDATE command_acknowledgments
        SET status = 'failed', error_message = %s
        WHERE command_id = %s
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (error_message, command_id))


# ─────────────────────────────────────────────────────────────────────────────
# Device Shadow/Twin
# ─────────────────────────────────────────────────────────────────────────────

def init_device_shadow_table():
    """Initialize the device_shadow table for offline state queries."""
    sql = """
        CREATE TABLE IF NOT EXISTS device_shadow (
            bin_id VARCHAR(50) PRIMARY KEY REFERENCES bins(bin_id) ON DELETE CASCADE,
            reported_state JSONB NOT NULL DEFAULT '{}',
            desired_state JSONB NOT NULL DEFAULT '{}',
            last_reported_at TIMESTAMP,
            last_desired_at TIMESTAMP,
            version INT DEFAULT 1,
            metadata JSONB DEFAULT '{}'
        );
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql)


def update_device_shadow_reported(bin_id: str, state: dict):
    """Update the reported state of a device shadow."""
    import json
    sql = """
        INSERT INTO device_shadow (bin_id, reported_state, last_reported_at, version)
        VALUES (%s, %s, NOW(), 1)
        ON CONFLICT (bin_id) DO UPDATE SET
            reported_state = device_shadow.reported_state || %s,
            last_reported_at = NOW(),
            version = device_shadow.version + 1
    """
    state_json = json.dumps(state)
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id, state_json, state_json))


def update_device_shadow_desired(bin_id: str, state: dict):
    """Update the desired state of a device shadow."""
    import json
    sql = """
        INSERT INTO device_shadow (bin_id, desired_state, last_desired_at, version)
        VALUES (%s, %s, NOW(), 1)
        ON CONFLICT (bin_id) DO UPDATE SET
            desired_state = device_shadow.desired_state || %s,
            last_desired_at = NOW(),
            version = device_shadow.version + 1
    """
    state_json = json.dumps(state)
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id, state_json, state_json))


def get_device_shadow(bin_id: str) -> dict:
    """Get the full device shadow."""
    sql = "SELECT * FROM device_shadow WHERE bin_id = %s"
    with get_cursor() as cur:
        cur.execute(sql, (bin_id,))
        row = cur.fetchone()
        if row:
            return dict(row)
        return None


def get_device_shadow_delta(bin_id: str) -> dict:
    """Get the delta between reported and desired state."""
    shadow = get_device_shadow(bin_id)
    if not shadow:
        return None
    
    reported = shadow.get('reported_state', {})
    desired = shadow.get('desired_state', {})
    
    delta = {}
    for key, value in desired.items():
        if key not in reported or reported[key] != value:
            delta[key] = value
    
    return {
        "bin_id": bin_id,
        "delta": delta,
        "has_delta": len(delta) > 0,
        "version": shadow.get('version')
    }


# ─────────────────────────────────────────────────────────────────────────────
# Power Profiling
# ─────────────────────────────────────────────────────────────────────────────

def init_power_profile_table():
    """Initialize the power_profiles table for battery tracking."""
    sql = """
        CREATE TABLE IF NOT EXISTS power_profiles (
            id SERIAL PRIMARY KEY,
            bin_id VARCHAR(50) NOT NULL REFERENCES bins(bin_id) ON DELETE CASCADE,
            recorded_at TIMESTAMP DEFAULT NOW(),
            batt_v FLOAT NOT NULL,
            batt_pct FLOAT,
            charging BOOLEAN DEFAULT FALSE,
            power_source VARCHAR(20) DEFAULT 'battery',
            estimated_days_remaining FLOAT
        );
        CREATE INDEX IF NOT EXISTS idx_power_bin_id ON power_profiles(bin_id);
        CREATE INDEX IF NOT EXISTS idx_power_recorded_at ON power_profiles(recorded_at);
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql)


def record_power_reading(bin_id: str, batt_v: float, batt_pct: float = None, 
                         charging: bool = False, power_source: str = 'battery'):
    """Record a power/battery reading."""
    # Calculate estimated days remaining based on drain rate
    estimated_days = calculate_battery_days_remaining(bin_id, batt_v)
    
    sql = """
        INSERT INTO power_profiles (bin_id, batt_v, batt_pct, charging, power_source, estimated_days_remaining)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id, batt_v, batt_pct, charging, power_source, estimated_days))


def calculate_battery_days_remaining(bin_id: str, current_voltage: float) -> float:
    """Calculate estimated days of battery remaining based on drain rate."""
    from datetime import datetime, timedelta, timezone
    
    # Get readings from the last 7 days
    sql = """
        SELECT batt_v, recorded_at
        FROM power_profiles
        WHERE bin_id = %s AND recorded_at > NOW() - INTERVAL '7 days'
        ORDER BY recorded_at ASC
        LIMIT 100
    """
    with get_cursor() as cur:
        cur.execute(sql, (bin_id,))
        readings = cur.fetchall()
    
    if len(readings) < 2:
        return None
    
    # Calculate voltage drain rate (V per day)
    first = readings[0]
    last = readings[-1]
    
    if first['recorded_at'] and last['recorded_at']:
        # Make both timezone-aware if needed
        first_time = first['recorded_at']
        last_time = last['recorded_at']
        if first_time.tzinfo is None:
            first_time = first_time.replace(tzinfo=timezone.utc)
        if last_time.tzinfo is None:
            last_time = last_time.replace(tzinfo=timezone.utc)
            
        time_diff = (last_time - first_time).total_seconds() / 86400  # days
        if time_diff > 0:
            voltage_drop = first['batt_v'] - last['batt_v']
            drain_rate = voltage_drop / time_diff  # V per day
            
            if drain_rate > 0:
                # Assume device dies at 3.0V
                remaining_voltage = current_voltage - 3.0
                days_remaining = remaining_voltage / drain_rate
                return round(days_remaining, 1)
    
    return None


def get_power_profile(bin_id: str, days: int = 30) -> dict:
    """Get power profile for a device."""
    sql = """
        SELECT 
            AVG(batt_v) as avg_voltage,
            MIN(batt_v) as min_voltage,
            MAX(batt_v) as max_voltage,
            COUNT(*) as reading_count
        FROM power_profiles
        WHERE bin_id = %s AND recorded_at > NOW() - INTERVAL '%s days'
    """
    with get_cursor() as cur:
        cur.execute(sql, (bin_id, days))
        stats = cur.fetchone()
    
    # Get recent readings
    sql2 = """
        SELECT batt_v, batt_pct, recorded_at, charging, estimated_days_remaining
        FROM power_profiles
        WHERE bin_id = %s
        ORDER BY recorded_at DESC
        LIMIT 50
    """
    with get_cursor() as cur:
        cur.execute(sql2, (bin_id,))
        readings = cur.fetchall()
    
    return {
        "bin_id": bin_id,
        "stats": dict(stats) if stats else {},
        "recent_readings": [dict(r) for r in readings],
        "days_analyzed": days
    }


# ─────────────────────────────────────────────────────────────────────────────
# OTA Firmware Updates
# ─────────────────────────────────────────────────────────────────────────────

def init_firmware_table():
    """Initialize firmware tracking tables."""
    sql = """
        CREATE TABLE IF NOT EXISTS firmware_versions (
            id SERIAL PRIMARY KEY,
            version VARCHAR(50) UNIQUE NOT NULL,
            release_date TIMESTAMP DEFAULT NOW(),
            file_url TEXT,
            file_size_kb INT,
            checksum VARCHAR(64),
            changelog TEXT,
            is_stable BOOLEAN DEFAULT FALSE,
            min_battery_pct INT DEFAULT 20
        );
        
        CREATE TABLE IF NOT EXISTS firmware_updates (
            id SERIAL PRIMARY KEY,
            bin_id VARCHAR(50) NOT NULL,
            target_version VARCHAR(50) NOT NULL,
            current_version VARCHAR(50),
            status VARCHAR(20) DEFAULT 'pending',
            started_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP,
            progress_pct INT DEFAULT 0,
            error_message TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_fw_updates_bin_id ON firmware_updates(bin_id);
        CREATE INDEX IF NOT EXISTS idx_fw_updates_status ON firmware_updates(status);
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql)


def create_firmware_version(version: str, file_url: str = None, file_size_kb: int = None,
                            checksum: str = None, changelog: str = None, is_stable: bool = False):
    """Create a new firmware version record."""
    sql = """
        INSERT INTO firmware_versions (version, file_url, file_size_kb, checksum, changelog, is_stable)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (version) DO UPDATE SET
            file_url = EXCLUDED.file_url,
            file_size_kb = EXCLUDED.file_size_kb,
            checksum = EXCLUDED.checksum,
            changelog = EXCLUDED.changelog,
            is_stable = EXCLUDED.is_stable
        RETURNING id
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (version, file_url, file_size_kb, checksum, changelog, is_stable))
        result = cur.fetchone()
        return result['id'] if result else None


def get_latest_firmware(stable_only: bool = True) -> dict:
    """Get the latest firmware version."""
    sql = """
        SELECT * FROM firmware_versions
        WHERE is_stable = TRUE OR %s = FALSE
        ORDER BY release_date DESC
        LIMIT 1
    """
    with get_cursor() as cur:
        cur.execute(sql, (stable_only,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_firmware_update(bin_id: str, target_version: str, current_version: str = None) -> int:
    """Create a firmware update job."""
    sql = """
        INSERT INTO firmware_updates (bin_id, target_version, current_version)
        VALUES (%s, %s, %s)
        RETURNING id
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id, target_version, current_version))
        result = cur.fetchone()
        return result['id'] if result else None


def update_firmware_progress(bin_id: str, progress_pct: int, status: str = None):
    """Update firmware update progress."""
    if status:
        sql = """
            UPDATE firmware_updates
            SET progress_pct = %s, status = %s, completed_at = CASE WHEN %s IN ('completed', 'failed') THEN NOW() ELSE NULL END
            WHERE bin_id = %s AND status NOT IN ('completed', 'failed')
            ORDER BY started_at DESC
            LIMIT 1
        """
        with get_cursor(commit=True) as cur:
            cur.execute(sql, (progress_pct, status, status, bin_id))
    else:
        sql = """
            UPDATE firmware_updates
            SET progress_pct = %s
            WHERE bin_id = %s AND status = 'in_progress'
        """
        with get_cursor(commit=True) as cur:
            cur.execute(sql, (progress_pct, bin_id))


def get_pending_firmware_updates(zone_prefix: str = None) -> list:
    """Get pending firmware updates, optionally filtered by zone."""
    if zone_prefix:
        sql = """
            SELECT fu.*, b.last_seen, b.device_status
            FROM firmware_updates fu
            JOIN bins b ON fu.bin_id = b.bin_id
            WHERE fu.status = 'pending' AND fu.bin_id LIKE %s
            ORDER BY fu.started_at ASC
        """
        with get_cursor() as cur:
            cur.execute(sql, (f"{zone_prefix}%",))
            return cur.fetchall()
    else:
        sql = """
            SELECT fu.*, b.last_seen, b.device_status
            FROM firmware_updates fu
            JOIN bins b ON fu.bin_id = b.bin_id
            WHERE fu.status = 'pending'
            ORDER BY fu.started_at ASC
        """
        with get_cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()


# ─────────────────────────────────────────────────────────────────────────────
# Diagnostic Mode
# ─────────────────────────────────────────────────────────────────────────────

def init_diagnostics_table():
    """Initialize diagnostics table."""
    sql = """
        CREATE TABLE IF NOT EXISTS device_diagnostics (
            id SERIAL PRIMARY KEY,
            bin_id VARCHAR(50) NOT NULL,
            requested_at TIMESTAMP DEFAULT NOW(),
            received_at TIMESTAMP,
            diagnostic_type VARCHAR(50) DEFAULT 'full',
            data JSONB,
            status VARCHAR(20) DEFAULT 'pending'
        );
        CREATE INDEX IF NOT EXISTS idx_diag_bin_id ON device_diagnostics(bin_id);
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql)


def request_diagnostic(bin_id: str, diagnostic_type: str = 'full') -> int:
    """Create a diagnostic request."""
    sql = """
        INSERT INTO device_diagnostics (bin_id, diagnostic_type)
        VALUES (%s, %s)
        RETURNING id
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id, diagnostic_type))
        result = cur.fetchone()
        return result['id'] if result else None


def store_diagnostic_result(bin_id: str, data: dict, diagnostic_id: int = None):
    """Store diagnostic result from device."""
    import json
    if diagnostic_id:
        sql = """
            UPDATE device_diagnostics
            SET received_at = NOW(), data = %s, status = 'received'
            WHERE id = %s
        """
        with get_cursor(commit=True) as cur:
            cur.execute(sql, (json.dumps(data), diagnostic_id))
    else:
        # Update most recent pending diagnostic for this bin
        sql = """
            UPDATE device_diagnostics
            SET received_at = NOW(), data = %s, status = 'received'
            WHERE bin_id = %s AND status = 'pending'
            ORDER BY requested_at DESC
            LIMIT 1
        """
        with get_cursor(commit=True) as cur:
            cur.execute(sql, (json.dumps(data), bin_id))


def get_device_diagnostics(bin_id: str, limit: int = 10) -> list:
    """Get diagnostic history for a device."""
    sql = """
        SELECT * FROM device_diagnostics
        WHERE bin_id = %s
        ORDER BY requested_at DESC
        LIMIT %s
    """
    with get_cursor() as cur:
        cur.execute(sql, (bin_id, limit))
        return [dict(r) for r in cur.fetchall()]


# ─────────────────────────────────────────────────────────────────────────────
# Device Provisioning
# ─────────────────────────────────────────────────────────────────────────────

def init_provisioning_table():
    """Initialize device provisioning table."""
    sql = """
        CREATE TABLE IF NOT EXISTS device_credentials (
            bin_id VARCHAR(50) PRIMARY KEY,
            mqtt_username VARCHAR(100) NOT NULL,
            mqtt_password_hash VARCHAR(200) NOT NULL,
            provisioned_at TIMESTAMP DEFAULT NOW(),
            provisioned_by VARCHAR(100),
            revoked BOOLEAN DEFAULT FALSE,
            revoked_at TIMESTAMP
        );
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql)


def provision_device(bin_id: str, mqtt_username: str, mqtt_password_hash: str, 
                     provisioned_by: str = None) -> bool:
    """Store device provisioning credentials."""
    sql = """
        INSERT INTO device_credentials (bin_id, mqtt_username, mqtt_password_hash, provisioned_by)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (bin_id) DO UPDATE SET
            mqtt_username = EXCLUDED.mqtt_username,
            mqtt_password_hash = EXCLUDED.mqtt_password_hash,
            provisioned_at = NOW(),
            provisioned_by = EXCLUDED.provisioned_by,
            revoked = FALSE,
            revoked_at = NULL
        RETURNING bin_id
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id, mqtt_username, mqtt_password_hash, provisioned_by))
        return cur.fetchone() is not None


def revoke_device_credentials(bin_id: str) -> bool:
    """Revoke device credentials."""
    sql = """
        UPDATE device_credentials
        SET revoked = TRUE, revoked_at = NOW()
        WHERE bin_id = %s
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (bin_id,))
        return cur.rowcount > 0


def get_device_credentials(bin_id: str) -> dict:
    """Get device credentials (without password)."""
    sql = """
        SELECT bin_id, mqtt_username, provisioned_at, provisioned_by, revoked
        FROM device_credentials
        WHERE bin_id = %s
    """
    with get_cursor() as cur:
        cur.execute(sql, (bin_id,))
        row = cur.fetchone()
        return dict(row) if row else None


# ─────────────────────────────────────────────────────────────────────────────
# Initialize All IoT Tables
# ─────────────────────────────────────────────────────────────────────────────

def init_all_iot_tables():
    """Initialize all IoT-related tables."""
    init_heartbeat_table()
    init_command_ack_table()
    init_device_shadow_table()
    init_power_profile_table()
    init_firmware_table()
    init_diagnostics_table()
    init_provisioning_table()
