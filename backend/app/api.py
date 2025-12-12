"""
FastAPI routes for CleanRoute Backend.
Exposes endpoints for the Planner UI.
"""
from typing import Optional, List
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
# Future Endpoints (Phase 3 - EWMA Forecasting)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/bins/at_risk")
async def get_bins_at_risk():
    """
    Get bins at risk of overflow.
    TODO: Implement EWMA-based TTF prediction.
    """
    # Placeholder for Phase 3
    return {
        "message": "Coming soon - EWMA overflow prediction",
        "bins_at_risk": []
    }
