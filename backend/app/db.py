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
    """
    sql = """
        INSERT INTO bins (bin_id, lat, lon, last_seen)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (bin_id) DO UPDATE SET
            lat = EXCLUDED.lat,
            lon = EXCLUDED.lon,
            last_seen = EXCLUDED.last_seen
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
    """
    sql = """
        SELECT DISTINCT ON (b.bin_id)
            b.bin_id,
            b.lat,
            b.lon,
            b.last_seen,
            b.last_emptied,
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
