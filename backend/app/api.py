"""
FastAPI routes for CleanRoute Backend.
Exposes endpoints for the Planner UI.
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from datetime import datetime

from . import db
from . import mqtt_ingest

# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────────────────

class BinLatest(BaseModel):
    """Latest state of a bin."""
    bin_id: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    last_seen: Optional[datetime] = None
    last_emptied: Optional[datetime] = None
    fill_pct: Optional[float] = None
    batt_v: Optional[float] = None
    temp_c: Optional[float] = None
    last_telemetry_ts: Optional[datetime] = None


class TelemetryRecord(BaseModel):
    """Single telemetry reading."""
    id: int
    ts: datetime
    bin_id: str
    fill_pct: float
    batt_v: Optional[float] = None
    temp_c: Optional[float] = None
    emptied: bool = False
    lat: Optional[float] = None
    lon: Optional[float] = None
    received_at: datetime


class HealthStatus(BaseModel):
    """System health status."""
    status: str
    database: bool
    mqtt: dict
    timestamp: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Health check endpoint.
    Returns status of database and MQTT connections.
    """
    db_ok = db.check_db_connection()
    mqtt_status = mqtt_ingest.get_ingest_status()
    
    return HealthStatus(
        status="ok" if db_ok and mqtt_status["connected"] else "degraded",
        database=db_ok,
        mqtt=mqtt_status,
        timestamp=datetime.utcnow()
    )


@router.get("/bins/latest", response_model=List[BinLatest])
async def get_bins_latest():
    """
    Get latest state of all bins.
    Returns one row per bin with the most recent fill percentage, 
    coordinates, and timestamps.
    """
    try:
        rows = db.get_all_bins_latest()
        return [BinLatest(**dict(row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/telemetry/recent", response_model=List[TelemetryRecord])
async def get_recent_telemetry(
    bin_id: str = Query(..., description="Bin ID to fetch telemetry for"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """
    Get recent telemetry records for a specific bin.
    Returns the most recent N records ordered by timestamp descending.
    """
    try:
        rows = db.get_recent_telemetry(bin_id, limit)
        if not rows:
            raise HTTPException(status_code=404, detail=f"No telemetry found for bin: {bin_id}")
        return [TelemetryRecord(**dict(row)) for row in rows]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# ML Prediction & Route Optimization Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/bins/forecast")
async def forecast_bins(
    target_time: Optional[str] = Query(None, description="ISO datetime or preset: tomorrow_morning, tomorrow_afternoon, 6h, 24h, 48h"),
    threshold: float = Query(80.0, ge=0, le=100, description="Fill percentage threshold for collection")
):
    """
    Predict fill levels for all bins at a specific future time.
    
    Args:
        target_time: Future time (ISO format or preset)
        threshold: Minimum fill % to mark as needing collection
    
    Returns:
        Predictions for all bins
    """
    from . import ml_prediction
    from dateutil import parser as date_parser
    
    try:
        # Parse target time
        if target_time is None:
            # Default to tomorrow afternoon
            target_dt = ml_prediction.parse_preset_time('tomorrow_afternoon')
        elif target_time in ['tomorrow_morning', 'tomorrow_afternoon', '6h', '24h', '48h']:
            target_dt = ml_prediction.parse_preset_time(target_time)
        else:
            target_dt = date_parser.parse(target_time)
        
        # Get predictions
        result = ml_prediction.forecast_all_bins(target_dt, threshold)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bins/{bin_id}/prediction")
async def get_bin_prediction(
    bin_id: str,
    target_time: Optional[str] = Query(None, description="ISO datetime or preset")
):
    """
    Get detailed prediction for a specific bin.
    
    Args:
        bin_id: Bin identifier
        target_time: Future time to predict
    
    Returns:
        Detailed prediction with fill rate, confidence, etc.
    """
    from . import ml_prediction
    from dateutil import parser as date_parser
    
    try:
        # Parse target time
        if target_time is None:
            target_dt = ml_prediction.parse_preset_time('tomorrow_afternoon')
        elif target_time in ['tomorrow_morning', 'tomorrow_afternoon', '6h', '24h', '48h']:
            target_dt = ml_prediction.parse_preset_time(target_time)
        else:
            target_dt = date_parser.parse(target_time)
        
        # Get prediction
        prediction = ml_prediction.predict_fill_at_time(bin_id, target_dt)
        
        if "error" in prediction:
            raise HTTPException(status_code=404, detail=prediction["error"])
        
        return prediction
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RouteOptimizationRequest(BaseModel):
    """Request body for route optimization."""
    target_time: Optional[str] = None  # ISO datetime or preset
    threshold_pct: float = 80.0
    depot_location: Optional[Dict[str, float]] = None  # {"lat": 6.9271, "lon": 79.8612, "name": "Office"}
    algorithm: str = "greedy"


@router.post("/routes/optimize")
async def optimize_route(request: RouteOptimizationRequest):
    """
    Generate optimal collection route based on predicted fill levels.
    
    Workflow:
    1. Predict fill levels at target time
    2. Filter bins that need collection (>= threshold)
    3. Optimize route using selected algorithm
    4. Return route with waypoints, distance, duration
    
    Args:
        request: Route optimization parameters
    
    Returns:
        Optimized route with waypoints and summary
    """
    from . import ml_prediction, route_optimizer
    from dateutil import parser as date_parser
    
    try:
        # Parse target time
        if request.target_time is None:
            target_dt = ml_prediction.parse_preset_time('tomorrow_afternoon')
        elif request.target_time in ['tomorrow_morning', 'tomorrow_afternoon', '6h', '24h', '48h']:
            target_dt = ml_prediction.parse_preset_time(request.target_time)
        else:
            target_dt = date_parser.parse(request.target_time)
        
        # Get bins that need collection
        bins_to_collect = ml_prediction.get_bins_needing_collection(
            target_dt, 
            request.threshold_pct
        )
        
        if not bins_to_collect:
            return {
                "message": "No bins need collection at the specified time and threshold",
                "target_time": target_dt.isoformat(),
                "threshold_pct": request.threshold_pct,
                "route": None
            }
        
        # Optimize route
        route_result = route_optimizer.optimize_route(
            bins_to_collect,
            request.depot_location,
            request.algorithm
        )
        
        # Add metadata
        route_result['target_time'] = target_dt.isoformat()
        route_result['threshold_pct'] = request.threshold_pct
        route_result['generated_at'] = datetime.utcnow().isoformat()
        
        return route_result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bins/at_risk")
async def get_bins_at_risk(
    threshold_hours: int = Query(48, ge=1, le=168, description="Hours until overflow threshold")
):
    """
    Get bins at risk of overflow (legacy endpoint - use /bins/forecast instead).
    
    This endpoint is kept for backward compatibility.
    """
    from . import ml_prediction
    from datetime import timedelta
    
    try:
        target_time = datetime.utcnow() + timedelta(hours=threshold_hours)
        bins = ml_prediction.get_bins_needing_collection(target_time, 80.0)
        
        return {
            "threshold_hours": threshold_hours,
            "target_time": target_time.isoformat(),
            "bins_at_risk": bins,
            "count": len(bins)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Device Management Endpoints
# ─────────────────────────────────────────────────────────────────────────────

class DeviceRegistration(BaseModel):
    """Device registration payload."""
    bin_id: str
    user_id: str
    user_name: str
    user_phone: str
    wifi_ssid: str
    lat: Optional[float] = None
    lon: Optional[float] = None


@router.post("/devices/register")
async def register_device(device: DeviceRegistration):
    """
    Register a new device with user information.
    Called during device setup process.
    """
    try:
        db.register_device(
            bin_id=device.bin_id,
            user_id=device.user_id,
            user_name=device.user_name,
            user_phone=device.user_phone,
            wifi_ssid=device.wifi_ssid,
            lat=device.lat,
            lon=device.lon
        )
        return {
            "success": True,
            "message": f"Device {device.bin_id} registered successfully",
            "bin_id": device.bin_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/user/{user_id}")
async def get_user_devices(user_id: str):
    """Get all devices registered to a user."""
    try:
        bins = db.get_user_bins(user_id)
        return {"user_id": user_id, "bins": [dict(b) for b in bins]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Device Health & Monitoring Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/devices/{bin_id}/health")
async def get_device_health(bin_id: str):
    """Get detailed health status for a specific device."""
    from . import alerts
    try:
        health = alerts.get_device_health(bin_id)
        if "error" in health:
            raise HTTPException(status_code=404, detail=health["error"])
        return health
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fleet/health")
async def get_fleet_health():
    """Get overall fleet health summary."""
    from . import alerts
    try:
        return alerts.get_fleet_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/health-check")
async def run_health_check():
    """
    Manually trigger health check for all devices.
    Creates alerts for battery, offline, and overflow issues.
    """
    from . import alerts
    try:
        summary = alerts.run_health_checks()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Alerts Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/alerts")
async def get_alerts(bin_id: Optional[str] = Query(None)):
    """Get unresolved alerts, optionally filtered by bin_id."""
    try:
        alerts_list = db.get_unresolved_alerts(bin_id)
        return {"alerts": [dict(a) for a in alerts_list]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int):
    """Mark an alert as resolved."""
    try:
        db.resolve_alert(alert_id)
        return {"success": True, "alert_id": alert_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Command & Control Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/commands/{bin_id}/wake")
async def wake_device(bin_id: str, collection_hours: int = Query(12, ge=1, le=24)):
    """Send wake-up command to a specific bin."""
    from . import mqtt_commands
    try:
        success = mqtt_commands.wake_up_bin(bin_id, collection_hours)
        return {
            "success": success,
            "bin_id": bin_id,
            "command": "wake_up",
            "collection_hours": collection_hours
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commands/{bin_id}/sleep")
async def sleep_device(bin_id: str):
    """Send sleep command to a specific bin."""
    from . import mqtt_commands
    try:
        success = mqtt_commands.sleep_bin(bin_id)
        return {"success": success, "bin_id": bin_id, "command": "sleep"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commands/{bin_id}/reset-emptied")
async def reset_emptied(bin_id: str):
    """Reset the emptied flag on a bin."""
    from . import mqtt_commands
    try:
        success = mqtt_commands.reset_emptied_flag(bin_id)
        return {"success": success, "bin_id": bin_id, "command": "reset_emptied"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commands/{bin_id}/status")
async def request_status(bin_id: str):
    """Request immediate status update from device."""
    from . import mqtt_commands
    try:
        success = mqtt_commands.request_status(bin_id)
        return {"success": success, "bin_id": bin_id, "command": "get_status"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commands/{bin_id}/history")
async def get_command_history(bin_id: str, limit: int = Query(50, ge=1, le=200)):
    """Get command history for a bin."""
    try:
        commands = db.get_command_history(bin_id, limit)
        return {"bin_id": bin_id, "commands": [dict(c) for c in commands]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Collection Day Workflow Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/collection/start")
async def start_collection_day(collection_hours: int = Query(12, ge=1, le=24)):
    """
    Start collection day workflow:
    - Wake up all bins
    - Create reminder alerts for users
    - Return status
    """
    from . import mqtt_commands
    try:
        result = mqtt_commands.start_collection_day(collection_hours)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collection/end")
async def end_collection_day():
    """
    End collection day workflow:
    - Send sleep command to all bins
    - Mark collection complete
    """
    from . import mqtt_commands
    try:
        result = mqtt_commands.end_collection_day()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collection/remind")
async def send_reminders():
    """
    Send reminder alerts to users whose bins are still offline.
    Used during collection day if devices haven't responded.
    """
    from . import alerts
    try:
        # Check for offline bins that should be awake
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT bin_id, user_name, user_phone
                FROM bins
                WHERE sleep_mode = FALSE 
                AND device_status = 'offline'
                AND user_id IS NOT NULL
            """)
            offline_bins = cur.fetchall()
        
        reminders_sent = []
        for bin_data in offline_bins:
            alert_id = db.create_alert(
                bin_id=bin_data['bin_id'],
                alert_type="collection_reminder",
                severity="warning",
                message=f"⚠️ Reminder: Please turn on bin device {bin_data['bin_id']}. User: {bin_data['user_name']}"
            )
            reminders_sent.append({
                "bin_id": bin_data['bin_id'],
                "user": bin_data['user_name'],
                "alert_id": alert_id
            })
        
        return {
            "success": True,
            "reminders_sent": len(reminders_sent),
            "bins": reminders_sent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
