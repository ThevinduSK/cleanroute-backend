"""
Alerts and Device Health Monitoring System

Monitors:
- Battery levels (< 3.5V critical)
- Device online/offline status
- Fill levels (> 90% overflow risk)
- Collection reminders
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from . import db

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Alert Thresholds (configurable)
# ─────────────────────────────────────────────────────────────────────────────
BATTERY_CRITICAL_V = 3.5
BATTERY_LOW_V = 3.7
FILL_WARNING_PCT = 80.0
FILL_CRITICAL_PCT = 90.0
OFFLINE_THRESHOLD_MINUTES = 60


# ─────────────────────────────────────────────────────────────────────────────
# Alert Types
# ─────────────────────────────────────────────────────────────────────────────

def check_battery_alerts() -> List[Dict[str, Any]]:
    """Check all bins for low battery and create alerts."""
    alerts_created = []
    
    with db.get_cursor() as cur:
        cur.execute("""
            SELECT b.bin_id, t.batt_v, b.user_name, b.user_phone
            FROM bins b
            JOIN LATERAL (
                SELECT batt_v 
                FROM telemetry 
                WHERE bin_id = b.bin_id 
                ORDER BY ts DESC 
                LIMIT 1
            ) t ON true
            WHERE t.batt_v IS NOT NULL AND t.batt_v < %s
        """, (BATTERY_CRITICAL_V,))
        
        low_battery_bins = cur.fetchall()
    
    for bin_data in low_battery_bins:
        severity = "critical" if bin_data['batt_v'] < BATTERY_CRITICAL_V else "warning"
        message = f"Low battery: {bin_data['batt_v']:.2f}V (bin {bin_data['bin_id']})"
        
        if bin_data['user_name']:
            message += f" - User: {bin_data['user_name']}"
        
        alert_id = db.create_alert(
            bin_id=bin_data['bin_id'],
            alert_type="battery_low",
            severity=severity,
            message=message
        )
        
        alerts_created.append({
            "alert_id": alert_id,
            "bin_id": bin_data['bin_id'],
            "type": "battery_low",
            "battery_v": bin_data['batt_v']
        })
        
        logger.warning(f"Low battery: {message}")
    
    return alerts_created


def check_offline_bins() -> List[Dict[str, Any]]:
    """Check for bins that haven't sent data in a while."""
    alerts_created = []
    threshold_time = datetime.utcnow() - timedelta(minutes=OFFLINE_THRESHOLD_MINUTES)
    
    with db.get_cursor() as cur:
        cur.execute("""
            SELECT bin_id, last_seen, user_name, sleep_mode
            FROM bins
            WHERE last_seen < %s 
            AND sleep_mode = FALSE
            AND device_status != 'offline'
        """, (threshold_time,))
        
        offline_bins = cur.fetchall()
    
    for bin_data in offline_bins:
        minutes_ago = int((datetime.utcnow() - bin_data['last_seen'].replace(tzinfo=None)).total_seconds() / 60)
        message = f"Bin {bin_data['bin_id']} offline for {minutes_ago} minutes"
        
        if bin_data['user_name']:
            message += f" - User: {bin_data['user_name']}"
        
        alert_id = db.create_alert(
            bin_id=bin_data['bin_id'],
            alert_type="device_offline",
            severity="warning",
            message=message
        )
        
        # Update device status
        with db.get_cursor(commit=True) as update_cur:
            update_cur.execute(
                "UPDATE bins SET device_status = 'offline' WHERE bin_id = %s",
                (bin_data['bin_id'],)
            )
        
        alerts_created.append({
            "alert_id": alert_id,
            "bin_id": bin_data['bin_id'],
            "type": "device_offline",
            "offline_minutes": minutes_ago
        })
        
        logger.warning(f"Offline: {message}")
    
    return alerts_created


def check_overflow_risk() -> List[Dict[str, Any]]:
    """Check for bins at risk of overflow."""
    alerts_created = []
    
    with db.get_cursor() as cur:
        cur.execute("""
            SELECT b.bin_id, t.fill_pct, b.user_name, b.lat, b.lon
            FROM bins b
            JOIN LATERAL (
                SELECT fill_pct 
                FROM telemetry 
                WHERE bin_id = b.bin_id 
                ORDER BY ts DESC 
                LIMIT 1
            ) t ON true
            WHERE t.fill_pct >= %s
        """, (FILL_WARNING_PCT,))
        
        high_fill_bins = cur.fetchall()
    
    for bin_data in high_fill_bins:
        severity = "critical" if bin_data['fill_pct'] >= FILL_CRITICAL_PCT else "warning"
        message = f"High fill level: {bin_data['fill_pct']:.1f}% (bin {bin_data['bin_id']})"
        
        if bin_data['user_name']:
            message += f" - User: {bin_data['user_name']}"
        
        alert_id = db.create_alert(
            bin_id=bin_data['bin_id'],
            alert_type="overflow_risk",
            severity=severity,
            message=message
        )
        
        alerts_created.append({
            "alert_id": alert_id,
            "bin_id": bin_data['bin_id'],
            "type": "overflow_risk",
            "fill_pct": bin_data['fill_pct'],
            "lat": bin_data['lat'],
            "lon": bin_data['lon']
        })
        
        logger.warning(f"Overflow risk: {message}")
    
    return alerts_created


# ─────────────────────────────────────────────────────────────────────────────
# Device Health Status
# ─────────────────────────────────────────────────────────────────────────────

def get_device_health(bin_id: str) -> Dict[str, Any]:
    """Get comprehensive health status for a device."""
    with db.get_cursor() as cur:
        # Get latest telemetry
        cur.execute("""
            SELECT 
                b.*,
                t.fill_pct,
                t.batt_v,
                t.temp_c,
                t.ts as last_telemetry_ts,
                EXTRACT(EPOCH FROM (NOW() - b.last_seen))/60 as minutes_since_seen
            FROM bins b
            LEFT JOIN LATERAL (
                SELECT fill_pct, batt_v, temp_c, ts
                FROM telemetry 
                WHERE bin_id = b.bin_id 
                ORDER BY ts DESC 
                LIMIT 1
            ) t ON true
            WHERE b.bin_id = %s
        """, (bin_id,))
        
        bin_data = cur.fetchone()
        
        if not bin_data:
            return {"error": "Bin not found"}
        
        # Calculate status
        is_online = bin_data['minutes_since_seen'] < OFFLINE_THRESHOLD_MINUTES if bin_data['minutes_since_seen'] else False
        battery_status = "ok"
        if bin_data['batt_v']:
            if bin_data['batt_v'] < BATTERY_CRITICAL_V:
                battery_status = "critical"
            elif bin_data['batt_v'] < BATTERY_LOW_V:
                battery_status = "low"
        
        fill_status = "ok"
        if bin_data['fill_pct']:
            if bin_data['fill_pct'] >= FILL_CRITICAL_PCT:
                fill_status = "critical"
            elif bin_data['fill_pct'] >= FILL_WARNING_PCT:
                fill_status = "warning"
        
        # Get unresolved alerts
        cur.execute("""
            SELECT COUNT(*) as alert_count
            FROM alerts
            WHERE bin_id = %s AND resolved = FALSE
        """, (bin_id,))
        alert_count = cur.fetchone()['alert_count']
        
        return {
            "bin_id": bin_id,
            "online": is_online,
            "sleep_mode": bin_data['sleep_mode'],
            "battery": {
                "voltage": bin_data['batt_v'],
                "status": battery_status
            },
            "fill": {
                "percentage": bin_data['fill_pct'],
                "status": fill_status
            },
            "last_seen": bin_data['last_seen'].isoformat() if bin_data['last_seen'] else None,
            "minutes_since_seen": int(bin_data['minutes_since_seen']) if bin_data['minutes_since_seen'] else None,
            "user": {
                "id": bin_data['user_id'],
                "name": bin_data['user_name'],
                "phone": bin_data['user_phone']
            },
            "unresolved_alerts": alert_count,
            "firmware_version": bin_data['firmware_version']
        }


def get_fleet_health() -> Dict[str, Any]:
    """Get health summary for all devices."""
    with db.get_cursor() as cur:
        cur.execute("""
            SELECT 
                COUNT(*) as total_bins,
                COUNT(*) FILTER (WHERE EXTRACT(EPOCH FROM (NOW() - last_seen))/60 < %s) as online_bins,
                COUNT(*) FILTER (WHERE sleep_mode = TRUE) as sleeping_bins
            FROM bins
        """, (OFFLINE_THRESHOLD_MINUTES,))
        
        stats = cur.fetchone()
        
        # Get alert summary
        cur.execute("""
            SELECT alert_type, severity, COUNT(*) as count
            FROM alerts
            WHERE resolved = FALSE
            GROUP BY alert_type, severity
        """)
        
        alert_summary = {}
        for row in cur.fetchall():
            alert_type = row['alert_type']
            if alert_type not in alert_summary:
                alert_summary[alert_type] = {}
            alert_summary[alert_type][row['severity']] = row['count']
    
    return {
        "total_bins": stats['total_bins'],
        "online_bins": stats['online_bins'],
        "offline_bins": stats['total_bins'] - stats['online_bins'],
        "sleeping_bins": stats['sleeping_bins'],
        "active_bins": stats['total_bins'] - stats['sleeping_bins'],
        "alert_summary": alert_summary
    }


# ─────────────────────────────────────────────────────────────────────────────
# Monitoring Loop (Run Periodically)
# ─────────────────────────────────────────────────────────────────────────────

def run_health_checks() -> Dict[str, Any]:
    """Run all health checks and return summary."""
    logger.info("Running health checks...")
    
    battery_alerts = check_battery_alerts()
    offline_alerts = check_offline_bins()
    overflow_alerts = check_overflow_risk()
    
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "alerts_created": {
            "battery_low": len(battery_alerts),
            "device_offline": len(offline_alerts),
            "overflow_risk": len(overflow_alerts)
        },
        "total_new_alerts": len(battery_alerts) + len(offline_alerts) + len(overflow_alerts)
    }
    
    logger.info(f"Health check complete: {summary['total_new_alerts']} new alerts")
    return summary
