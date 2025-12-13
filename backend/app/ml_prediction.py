"""
ML Prediction Module - EWMA-based Fill Level Forecasting

Predicts future fill levels for bins using Exponentially Weighted Moving Average (EWMA).
Approach: Given a target time, predict what fill level each bin will have.

Data Sources:
- Primary: PostgreSQL database (real-time data)
- Alternative: CSV files (for testing/training with mock data)
"""
import logging
import os
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dateutil import parser as date_parser
from . import db

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
EWMA_ALPHA = 0.3  # Smoothing factor (0-1), higher = more weight on recent data
MIN_DATA_POINTS = 5  # Minimum historical points needed for prediction
MAX_HISTORY_DAYS = 30  # Look back up to 30 days
DEFAULT_FILL_RATE = 1.5  # Default fill rate (% per hour) if no history

# CSV data source (optional)
CSV_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "mock_data")
USE_CSV_DATA = os.getenv("USE_CSV_DATA", "false").lower() == "true"


# ─────────────────────────────────────────────────────────────────────────────
# CSV Data Source (Alternative to Database)
# ─────────────────────────────────────────────────────────────────────────────

def load_telemetry_from_csv(bin_id: str, days: int = MAX_HISTORY_DAYS) -> List[Dict]:
    """
    Load historical telemetry from CSV file (alternative to database).
    
    Args:
        bin_id: Bin identifier
        days: Number of days to look back
    
    Returns:
        List of telemetry records
    """
    csv_path = os.path.join(CSV_DATA_DIR, "telemetry_data.csv")
    
    if not os.path.exists(csv_path):
        logger.warning(f"CSV file not found: {csv_path}")
        return []
    
    try:
        records = []
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['bin_id'] == bin_id:
                    ts = date_parser.parse(row['ts'])
                    if ts >= cutoff_date:
                        records.append({
                            'ts': ts,
                            'fill_pct': float(row['fill_pct'])
                        })
        
        # Sort by timestamp
        records.sort(key=lambda x: x['ts'])
        logger.info(f"Loaded {len(records)} records from CSV for {bin_id}")
        return records
        
    except Exception as e:
        logger.error(f"Error loading CSV data: {e}")
        return []


def get_historical_data(bin_id: str, days: int = MAX_HISTORY_DAYS) -> List[Dict]:
    """
    Get historical telemetry data from database or CSV.
    
    Args:
        bin_id: Bin identifier
        days: Number of days to look back
    
    Returns:
        List of telemetry records with 'ts' and 'fill_pct'
    """
    if USE_CSV_DATA:
        return load_telemetry_from_csv(bin_id, days)
    else:
        # Use database (existing logic)
        try:
            with db.get_cursor() as cur:
                cur.execute("""
                    SELECT ts, fill_pct
                    FROM telemetry
                    WHERE bin_id = %s
                        AND ts >= NOW() - INTERVAL '%s days'
                        AND fill_pct IS NOT NULL
                    ORDER BY ts ASC
                """, (bin_id, days))
                
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching from database: {e}")
            return []


# ─────────────────────────────────────────────────────────────────────────────
# Core EWMA Calculation
# ─────────────────────────────────────────────────────────────────────────────

def calculate_ewma_fill_rate(bin_id: str, alpha: float = EWMA_ALPHA) -> Tuple[Optional[float], str]:
    """
    Calculate exponentially weighted moving average of fill rate for a bin.
    
    Args:
        bin_id: Bin identifier
        alpha: Smoothing factor (0-1), higher = more weight on recent values
    
    Returns:
        (fill_rate_per_hour, confidence_level)
        fill_rate_per_hour: Percentage increase per hour (e.g., 2.5 = 2.5% per hour)
        confidence_level: 'high', 'medium', 'low', or None if insufficient data
    """
    try:
        # Get historical telemetry data (database or CSV)
        history = get_historical_data(bin_id, MAX_HISTORY_DAYS)
        
        if len(history) < MIN_DATA_POINTS:
            logger.warning(f"Insufficient data for {bin_id}: {len(history)} points (need {MIN_DATA_POINTS})")
            return None, "insufficient_data"
        
        # Calculate fill rates between consecutive readings
        fill_rates = []
        
        for i in range(1, len(history)):
            prev_ts = history[i-1]['ts']
            curr_ts = history[i]['ts']
            prev_fill = history[i-1]['fill_pct']
            curr_fill = history[i]['fill_pct']
            
            # Calculate time difference in hours
            time_diff = (curr_ts - prev_ts).total_seconds() / 3600
            
            if time_diff > 0:
                # Calculate fill change rate (% per hour)
                fill_change = curr_fill - prev_fill
                rate = fill_change / time_diff
                
                # Only consider positive rates (filling up, not being emptied)
                # Filter out unrealistic rates (sensor errors)
                if 0 <= rate <= 10:  # Max 10% per hour is reasonable
                    fill_rates.append(rate)
        
        if not fill_rates:
            logger.warning(f"No valid fill rates calculated for {bin_id}")
            return None, "no_valid_rates"
        
        # Apply EWMA smoothing
        ewma_rate = fill_rates[0]
        for rate in fill_rates[1:]:
            ewma_rate = alpha * rate + (1 - alpha) * ewma_rate
        
        # Determine confidence based on data quality
        confidence = "high"
        if len(history) < 15:
            confidence = "medium"
        if len(history) < 10:
            confidence = "low"
        
        logger.info(f"Bin {bin_id}: EWMA fill rate = {ewma_rate:.3f}% per hour ({confidence} confidence)")
        
        return ewma_rate, confidence
    
    except Exception as e:
        logger.error(f"Error calculating EWMA for {bin_id}: {e}")
        return None, "error"


# ─────────────────────────────────────────────────────────────────────────────
# Prediction Functions
# ─────────────────────────────────────────────────────────────────────────────

def predict_fill_at_time(bin_id: str, target_time: datetime) -> Dict[str, Any]:
    """
    Predict what fill level a bin will have at a specific future time.
    
    Args:
        bin_id: Bin identifier
        target_time: Future datetime to predict fill level
    
    Returns:
        Dictionary with prediction details
    """
    try:
        # Get current bin state
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT b.bin_id, b.lat, b.lon, b.last_seen, b.device_status,
                       t.fill_pct as current_fill, t.ts as current_ts
                FROM bins b
                LEFT JOIN LATERAL (
                    SELECT fill_pct, ts
                    FROM telemetry
                    WHERE bin_id = b.bin_id
                    ORDER BY ts DESC
                    LIMIT 1
                ) t ON true
                WHERE b.bin_id = %s
            """, (bin_id,))
            
            bin_data = cur.fetchone()
        
        if not bin_data:
            return {"error": "Bin not found", "bin_id": bin_id}
        
        current_fill = bin_data['current_fill']
        
        if current_fill is None:
            return {
                "bin_id": bin_id,
                "error": "No telemetry data",
                "needs_collection": False,
                "confidence": "none"
            }
        
        # Calculate fill rate
        fill_rate, confidence = calculate_ewma_fill_rate(bin_id)
        
        # If no valid fill rate, use current fill (assume no change)
        if fill_rate is None:
            predicted_fill = current_fill
            confidence = "low"
        else:
            # Calculate hours until target time
            current_time = datetime.utcnow()
            hours_until_target = (target_time - current_time).total_seconds() / 3600
            
            # Predict future fill level
            predicted_fill = current_fill + (fill_rate * hours_until_target)
            
            # Cap at 100% (can't overflow beyond capacity)
            predicted_fill = min(predicted_fill, 100.0)
            
            # If prediction is less than current (decreasing trend), use current
            if predicted_fill < current_fill:
                predicted_fill = current_fill
        
        return {
            "bin_id": bin_id,
            "lat": bin_data['lat'],
            "lon": bin_data['lon'],
            "current_fill": round(current_fill, 1),
            "predicted_fill": round(predicted_fill, 1),
            "fill_rate_per_hour": round(fill_rate, 3) if fill_rate else None,
            "prediction_time": target_time.isoformat(),
            "confidence": confidence,
            "device_status": bin_data['device_status'],
            "needs_collection": predicted_fill >= 80.0,  # Default threshold
            "last_seen": bin_data['last_seen'].isoformat() if bin_data['last_seen'] else None
        }
    
    except Exception as e:
        logger.error(f"Error predicting fill for {bin_id}: {e}")
        return {"error": str(e), "bin_id": bin_id}


def forecast_all_bins(target_time: datetime, threshold_pct: float = 80.0) -> Dict[str, Any]:
    """
    Predict fill levels for ALL bins at a specific future time.
    
    Args:
        target_time: Future datetime to predict
        threshold_pct: Fill percentage threshold for collection (default 80%)
    
    Returns:
        Dictionary with predictions for all bins
    """
    try:
        # Get all bins
        with db.get_cursor() as cur:
            cur.execute("SELECT bin_id FROM bins ORDER BY bin_id")
            all_bins = cur.fetchall()
        
        predictions = []
        bins_needing_collection = 0
        
        for bin_row in all_bins:
            bin_id = bin_row['bin_id']
            prediction = predict_fill_at_time(bin_id, target_time)
            
            if "error" not in prediction:
                # Update needs_collection based on custom threshold
                prediction['needs_collection'] = prediction['predicted_fill'] >= threshold_pct
                
                if prediction['needs_collection']:
                    bins_needing_collection += 1
                
                predictions.append(prediction)
        
        return {
            "target_time": target_time.isoformat(),
            "threshold_pct": threshold_pct,
            "predictions": predictions,
            "total_bins": len(predictions),
            "bins_needing_collection": bins_needing_collection
        }
    
    except Exception as e:
        logger.error(f"Error forecasting all bins: {e}")
        return {"error": str(e)}


def get_bins_needing_collection(target_time: datetime, threshold_pct: float = 80.0) -> List[Dict[str, Any]]:
    """
    Get list of bins that will need collection at target time.
    Filters bins with predicted fill >= threshold and valid GPS coordinates.
    
    Args:
        target_time: Future datetime
        threshold_pct: Minimum fill percentage for collection
    
    Returns:
        List of bins that need collection with their predicted states
    """
    forecast = forecast_all_bins(target_time, threshold_pct)
    
    if "error" in forecast:
        return []
    
    # Filter bins that need collection and have valid coordinates
    bins_to_collect = [
        bin_pred for bin_pred in forecast['predictions']
        if bin_pred['needs_collection']
        and bin_pred['lat'] is not None
        and bin_pred['lon'] is not None
        and bin_pred['device_status'] != 'offline'  # Don't include offline bins
    ]
    
    # Sort by predicted fill (highest first)
    bins_to_collect.sort(key=lambda x: x['predicted_fill'], reverse=True)
    
    logger.info(f"Found {len(bins_to_collect)} bins needing collection at {target_time}")
    
    return bins_to_collect


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def parse_preset_time(preset: str) -> datetime:
    """
    Convert preset time option to datetime.
    
    Args:
        preset: One of 'tomorrow_morning', 'tomorrow_afternoon', '6h', '24h', '48h'
    
    Returns:
        Target datetime
    """
    now = datetime.utcnow()
    
    if preset == 'tomorrow_morning':
        # Tomorrow at 8 AM
        tomorrow = now + timedelta(days=1)
        return datetime(tomorrow.year, tomorrow.month, tomorrow.day, 8, 0, 0)
    
    elif preset == 'tomorrow_afternoon':
        # Tomorrow at 2 PM
        tomorrow = now + timedelta(days=1)
        return datetime(tomorrow.year, tomorrow.month, tomorrow.day, 14, 0, 0)
    
    elif preset == '6h':
        return now + timedelta(hours=6)
    
    elif preset == '24h':
        return now + timedelta(hours=24)
    
    elif preset == '48h':
        return now + timedelta(hours=48)
    
    else:
        raise ValueError(f"Unknown preset: {preset}")
