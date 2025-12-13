"""
CleanRoute Frontend Server
Modern web interface for waste bin monitoring and route optimization

Integrates with FastAPI backend (PostgreSQL) with CSV fallback
"""
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import requests

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.route_optimizer import optimize_route, optimize_zone_routes, get_zone_info

app = Flask(__name__)
CORS(app)

# =============================================================================
# CONFIGURATION
# =============================================================================
# FastAPI backend URL (PostgreSQL)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/api")

# Set to True to use FastAPI backend, False to use CSV files
USE_BACKEND = os.environ.get("USE_BACKEND", "true").lower() == "true"

# Path to mock data (fallback)
MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'mock_data')

# EWMA configuration
# EWMA configuration
EWMA_ALPHA = 0.3

def calculate_fill_rate_ewma(history_df):
    """Calculate fill rate using EWMA on historical data, considering emptying events"""
    if len(history_df) < 2:
        return 1.5  # Default fill rate per hour
    
    # Sort by timestamp
    history_df = history_df.sort_values('timestamp').copy()
    
    # Find the most recent emptying event
    if 'emptied' in history_df.columns:
        emptied_events = history_df[history_df['emptied'] == True]
        if not emptied_events.empty:
            last_empty_time = emptied_events['timestamp'].max()
            # Only consider data after the last emptying
            history_df = history_df[history_df['timestamp'] > last_empty_time].copy()
    
    if len(history_df) < 2:
        return 1.5  # Not enough data after emptying
    
    # Calculate time differences in hours and fill level changes
    history_df['time_diff_hours'] = history_df['timestamp'].diff().dt.total_seconds() / 3600
    history_df['fill_diff'] = history_df['fill_level'].diff()
    
    # Remove rows where time_diff is 0 or negative, or where bin was emptied
    valid_rows = history_df[
        (history_df['time_diff_hours'] > 0) & 
        (history_df['fill_diff'] > 0) &  # Only positive fill changes
        (history_df['fill_diff'] < 50)  # Ignore unrealistic jumps
    ].copy()
    
    if len(valid_rows) == 0:
        return 1.5
    
    # Calculate fill rate per hour for each interval
    valid_rows.loc[:, 'fill_rate'] = valid_rows['fill_diff'] / valid_rows['time_diff_hours']
    
    # Apply EWMA
    ewma_rates = []
    for rate in valid_rows['fill_rate']:
        if len(ewma_rates) == 0:
            ewma_rates.append(rate)
        else:
            ewma_rates.append(EWMA_ALPHA * rate + (1 - EWMA_ALPHA) * ewma_rates[-1])
    
    # Return the most recent EWMA rate
    return max(0.1, ewma_rates[-1] if ewma_rates else 1.5)  # Minimum 0.1% per hour

def predict_bin_fill(bin_telemetry, target_time):
    """Predict fill level at target time using EWMA"""
    if bin_telemetry.empty:
        return {'predicted_fill_level': 0, 'confidence': 'none'}
    
    # Get latest reading
    latest = bin_telemetry.sort_values('timestamp', ascending=False).iloc[0]
    current_fill = float(latest['fill_level'])
    current_time = latest['timestamp']
    
    # Calculate fill rate
    fill_rate = calculate_fill_rate_ewma(bin_telemetry)
    
    # Calculate hours until target
    hours_diff = (target_time - current_time).total_seconds() / 3600
    
    # Predict fill level
    predicted_fill = current_fill + (fill_rate * hours_diff)
    predicted_fill = max(0, min(100, predicted_fill))  # Clamp between 0-100
    
    # Determine confidence
    if len(bin_telemetry) >= 20:
        confidence = 'high'
    elif len(bin_telemetry) >= 10:
        confidence = 'medium'
    else:
        confidence = 'low'
    
    return {
        'predicted_fill_level': predicted_fill,
        'confidence': confidence,
        'fill_rate': fill_rate
    }

def load_bins():
    """Load bin configuration from FastAPI backend (PostgreSQL) or CSV fallback"""
    
    # Try FastAPI backend first
    if USE_BACKEND:
        try:
            print(f"📡 Fetching bins from backend: {BACKEND_URL}/bins/latest")
            response = requests.get(f"{BACKEND_URL}/bins/latest", timeout=5)
            response.raise_for_status()
            bins_data = response.json()
            
            # Transform backend response to expected format
            bins = []
            for bin_info in bins_data:
                # Determine status: sleep_mode=True means offline, sleep_mode=False means active
                sleep_mode = bin_info.get('sleep_mode', True)
                status = 'offline' if sleep_mode else 'active'
                
                bins.append({
                    'bin_id': bin_info.get('bin_id'),
                    'latitude': bin_info.get('lat'),
                    'longitude': bin_info.get('lon'),
                    'location': bin_info.get('location', bin_info.get('bin_id')),
                    'type': bin_info.get('bin_type', 'general'),
                    'capacity_liters': bin_info.get('capacity_l', 120),
                    # Include live telemetry data from backend
                    'current_fill_level': bin_info.get('fill_pct', 0) if not sleep_mode else 0,
                    'battery_level': (bin_info.get('batt_v', 4.2) / 4.2 * 100) if not sleep_mode else 0,
                    'temperature': bin_info.get('temp_c') if not sleep_mode else None,
                    'last_updated': bin_info.get('last_seen'),
                    'status': status,
                    'sleep_mode': sleep_mode
                })
            
            print(f"✅ Loaded {len(bins)} bins from PostgreSQL backend")
            return bins
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Backend unavailable ({e}), falling back to CSV")
        except Exception as e:
            print(f"⚠️ Error parsing backend response: {e}")
    
    # Fallback to CSV
    try:
        csv_path = os.path.join(MOCK_DATA_PATH, 'bins_config.csv')
        print(f"📂 Loading bins from CSV: {csv_path}")
        bins_df = pd.read_csv(csv_path)
        
        # Rename columns to expected names
        bins_df = bins_df.rename(columns={
            'id': 'bin_id',
            'lat': 'latitude',
            'lon': 'longitude',
            'name': 'location'
        })
        
        # Add capacity_liters (default 240L for commercial, 120L for others)
        bins_df['capacity_liters'] = bins_df['type'].apply(lambda x: 240 if x == 'commercial' else 120)
        
        return bins_df.to_dict('records')
    except Exception as e:
        print(f"Error loading bins: {e}")
        import traceback
        traceback.print_exc()
        raise

def load_telemetry():
    """Load telemetry data from FastAPI backend (PostgreSQL) or CSV fallback"""
    
    # Try FastAPI backend first
    if USE_BACKEND:
        try:
            print(f"📡 Fetching telemetry from backend: {BACKEND_URL}/telemetry/recent")
            response = requests.get(f"{BACKEND_URL}/telemetry/recent?limit=500", timeout=5)
            response.raise_for_status()
            telemetry_data = response.json()
            
            # Transform backend response to DataFrame
            records = []
            for record in telemetry_data:
                battery_v = record.get('batt_v', 4.2)
                battery_pct = (battery_v / 4.2 * 100) if battery_v else 100
                
                records.append({
                    'bin_id': record.get('bin_id'),
                    'timestamp': pd.to_datetime(record.get('ts')),
                    'fill_level': record.get('fill_pct', 0),
                    'battery_voltage': battery_v,
                    'battery_level': min(100, max(0, battery_pct)),
                    'temperature': record.get('temp_c'),
                    'status': 'active' if battery_pct >= 20 else 'low_battery',
                    'emptied': record.get('emptied', False)
                })
            
            telemetry_df = pd.DataFrame(records)
            print(f"✅ Loaded {len(telemetry_df)} telemetry records from PostgreSQL backend")
            return telemetry_df
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Backend unavailable ({e}), falling back to CSV")
        except Exception as e:
            print(f"⚠️ Error parsing backend telemetry: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to CSV
    try:
        csv_path = os.path.join(MOCK_DATA_PATH, 'telemetry_data.csv')
        print(f"📂 Loading telemetry from CSV: {csv_path}")
        telemetry_df = pd.read_csv(csv_path)
        
        # Rename columns to expected names
        telemetry_df = telemetry_df.rename(columns={
            'ts': 'timestamp',
            'fill_pct': 'fill_level',
            'batt_v': 'battery_voltage',
            'temp_c': 'temperature'
        })
        
        # Convert battery voltage to percentage (assuming 4.2V = 100%)
        if 'battery_voltage' in telemetry_df.columns:
            telemetry_df['battery_level'] = (telemetry_df['battery_voltage'] / 4.2 * 100).clip(0, 100)
        
        # Add status based on battery and other conditions
        telemetry_df['status'] = 'active'
        telemetry_df.loc[telemetry_df['battery_level'] < 20, 'status'] = 'low_battery'
        
        telemetry_df['timestamp'] = pd.to_datetime(telemetry_df['timestamp'])
        return telemetry_df
    except Exception as e:
        print(f"Error loading telemetry: {e}")
        import traceback
        traceback.print_exc()
        raise

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/districts')
def districts():
    """Bins by district page"""
    return render_template('districts.html')

@app.route('/api/bins')
def get_bins():
    """Get all bins with current status"""
    try:
        bins = load_bins()
        telemetry_df = load_telemetry()
        
        # Add latest status to each bin
        for bin_data in bins:
            bin_id = bin_data['bin_id']
            bin_telemetry = telemetry_df[telemetry_df['bin_id'] == bin_id]
            
            if not bin_telemetry.empty:
                latest = bin_telemetry.sort_values('timestamp', ascending=False).iloc[0]
                bin_data['current_fill_level'] = float(latest['fill_level'])
                bin_data['battery_level'] = float(latest['battery_level'])
                bin_data['status'] = latest['status']
                bin_data['last_updated'] = latest['timestamp'].isoformat()
                
                # Calculate fill rate trend
                recent = bin_telemetry.tail(10)
                if len(recent) > 1:
                    fill_change = recent['fill_level'].diff().mean()
                    bin_data['fill_rate'] = float(fill_change) if not pd.isna(fill_change) else 0.0
                else:
                    bin_data['fill_rate'] = 0.0
            else:
                bin_data['current_fill_level'] = 0.0
                bin_data['battery_level'] = 100.0
                bin_data['status'] = 'unknown'
                bin_data['last_updated'] = None
                bin_data['fill_rate'] = 0.0
        
        return jsonify(bins)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bins/<bin_id>/history')
def get_bin_history(bin_id):
    """Get historical data for a specific bin"""
    try:
        telemetry_df = load_telemetry()
        bin_telemetry = telemetry_df[telemetry_df['bin_id'] == bin_id]
        
        history = []
        for _, row in bin_telemetry.iterrows():
            history.append({
                'timestamp': row['timestamp'].isoformat(),
                'fill_level': float(row['fill_level']),
                'battery_level': float(row['battery_level']),
                'temperature': float(row['temperature']) if not pd.isna(row['temperature']) else None,
                'status': row['status']
            })
        
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions/<target_time>')
def get_predictions(target_time):
    """Get predictions for all bins at target time"""
    try:
        telemetry_df = load_telemetry()
        bins = load_bins()
        
        print(f"Loaded {len(bins)} bins and {len(telemetry_df)} telemetry records")
        
        # Parse target time (format: YYYY-MM-DD-HH-MM)
        target_dt = datetime.strptime(target_time, '%Y-%m-%d-%H-%M')
        
        predictions = []
        for bin_data in bins:
            bin_id = bin_data['bin_id']
            bin_telemetry = telemetry_df[telemetry_df['bin_id'] == bin_id]
            
            if not bin_telemetry.empty:
                # Get current fill level
                latest = bin_telemetry.sort_values('timestamp', ascending=False).iloc[0]
                current_level = float(latest['fill_level'])
                
                # Predict fill level using EWMA
                prediction = predict_bin_fill(bin_telemetry, target_dt)
                
                predictions.append({
                    'bin_id': bin_id,
                    'location': bin_data['location'],
                    'latitude': bin_data['latitude'],
                    'longitude': bin_data['longitude'],
                    'current_fill_level': current_level,
                    'predicted_fill_level': prediction['predicted_fill_level'],
                    'confidence': prediction.get('confidence', 'medium'),
                    'will_overflow': prediction['predicted_fill_level'] >= 95,
                    'needs_collection': prediction['predicted_fill_level'] >= 70
                })
        
        print(f"Generated {len(predictions)} predictions")
        return jsonify(predictions)
    except Exception as e:
        print(f"ERROR in predictions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/route/<target_time>')
def get_route(target_time):
    """Get optimized collection route for target time"""
    try:
        telemetry_df = load_telemetry()
        bins = load_bins()
        
        # Parse target time
        target_dt = datetime.strptime(target_time, '%Y-%m-%d-%H-%M')
        
        # Get predictions for all bins
        bins_to_collect = []
        for bin_data in bins:
            bin_id = bin_data['bin_id']
            bin_telemetry = telemetry_df[telemetry_df['bin_id'] == bin_id]
            
            if not bin_telemetry.empty:
                # Predict fill level
                prediction = predict_bin_fill(bin_telemetry, target_dt)
                
                # Only include bins that need collection (>70% full)
                if prediction['predicted_fill_level'] >= 70:
                    bins_to_collect.append({
                        'bin_id': bin_id,
                        'name': bin_data['location'],
                        'lat': bin_data['latitude'],  # Use 'lat' key for optimizer
                        'lon': bin_data['longitude'],  # Use 'lon' key for optimizer
                        'capacity_l': bin_data['capacity_liters'],
                        'predicted_fill': prediction['predicted_fill_level'],  # Changed to 'predicted_fill'
                        'current_fill': bin_data.get('current_fill'),  # Optional current fill
                        'confidence': prediction.get('confidence', 'medium')  # Optional confidence
                    })
        
        # Optimize route
        if bins_to_collect:
            result = optimize_route(
                bins_to_collect=bins_to_collect,
                depot_location={'lat': 6.9271, 'lon': 79.8612}  # Independence Square
            )
            print(f"Generated route with {len(bins_to_collect)} bins")
            
            # Flatten the response structure for frontend
            route_data = result.get('route', {})
            waypoints = route_data.get('waypoints', [])
            summary = route_data.get('summary', {})
            
            # Transform waypoints to match frontend expectations
            transformed_waypoints = []
            for wp in waypoints:
                loc = wp.get('location', {})
                transformed_waypoints.append({
                    'type': wp.get('type', 'bin'),
                    'location': wp.get('name', 'Unknown'),  # Get name from waypoint
                    'latitude': loc.get('lat', 0),
                    'longitude': loc.get('lon', 0),
                    'predicted_fill_level': wp.get('predicted_fill', 0),  # Get predicted_fill from waypoint
                    'distance_from_previous': wp.get('distance_from_prev_km', 0)
                })
            
            return jsonify({
                'waypoints': transformed_waypoints,
                'total_distance_km': summary.get('total_distance_km', 0),
                'estimated_time_hours': summary.get('total_duration_min', 0) / 60,
                'bins_count': summary.get('total_bins', 0)
            })
        else:
            return jsonify({
                'waypoints': [],
                'total_distance_km': 0,
                'estimated_time_hours': 0,
                'bins_count': 0,
                'message': 'No bins need collection at this time'
            })
    except Exception as e:
        print(f"ERROR in route optimization: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    try:
        bins = load_bins()
        telemetry_df = load_telemetry()
        
        total_bins = len(bins)
        active_bins = 0
        full_bins = 0
        warning_bins = 0
        total_fill = 0
        
        for bin_data in bins:
            bin_id = bin_data['bin_id']
            bin_telemetry = telemetry_df[telemetry_df['bin_id'] == bin_id]
            
            if not bin_telemetry.empty:
                latest = bin_telemetry.sort_values('timestamp', ascending=False).iloc[0]
                fill_level = float(latest['fill_level'])
                
                if latest['status'] == 'active':
                    active_bins += 1
                
                if fill_level >= 90:
                    full_bins += 1
                elif fill_level >= 70:
                    warning_bins += 1
                
                total_fill += fill_level
        
        avg_fill = total_fill / total_bins if total_bins > 0 else 0
        
        return jsonify({
            'total_bins': total_bins,
            'active_bins': active_bins,
            'full_bins': full_bins,
            'warning_bins': warning_bins,
            'average_fill_level': round(avg_fill, 1),
            'offline_bins': total_bins - active_bins
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/zones')
def get_zones():
    """Get all zone definitions"""
    try:
        zones = get_zone_info()
        return jsonify(zones)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/zones/<zone_id>')
def get_zone(zone_id):
    """Get specific zone information"""
    try:
        zone = get_zone_info(zone_id)
        if zone:
            return jsonify(zone)
        else:
            return jsonify({'error': 'Zone not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/route-by-zone/<target_time>')
def get_route_by_zone(target_time):
    """Get optimized routes divided by zones for target time"""
    try:
        telemetry_df = load_telemetry()
        bins = load_bins()
        
        # Parse target time
        target_dt = datetime.strptime(target_time, '%Y-%m-%d-%H-%M')
        
        # Get predictions for all bins
        bins_to_collect = []
        for bin_data in bins:
            bin_id = bin_data['bin_id']
            bin_telemetry = telemetry_df[telemetry_df['bin_id'] == bin_id]
            
            if not bin_telemetry.empty:
                # Predict fill level
                prediction = predict_bin_fill(bin_telemetry, target_dt)
                
                # Only include bins that need collection (>70% full)
                if prediction['predicted_fill_level'] >= 70:
                    bins_to_collect.append({
                        'bin_id': bin_id,
                        'name': bin_data['location'],
                        'lat': bin_data['latitude'],
                        'lon': bin_data['longitude'],
                        'capacity_l': bin_data['capacity_liters'],
                        'predicted_fill': prediction['predicted_fill_level'],
                        'current_fill': bin_data.get('current_fill'),
                        'confidence': prediction.get('confidence', 'medium')
                    })
        
        # Optimize routes by zone
        if bins_to_collect:
            result = optimize_zone_routes(
                bins_to_collect=bins_to_collect,
                algorithm="greedy"
            )
            
            # Transform for frontend
            zones_data = []
            for zone in result.get('zones', []):
                waypoints = zone.get('waypoints', [])
                
                transformed_waypoints = []
                for wp in waypoints:
                    loc = wp.get('location', {})
                    transformed_waypoints.append({
                        'type': wp.get('type', 'bin'),
                        'bin_id': wp.get('bin_id'),
                        'location': wp.get('name', 'Unknown'),
                        'latitude': loc.get('lat', 0),
                        'longitude': loc.get('lon', 0),
                        'predicted_fill_level': wp.get('predicted_fill', 0),
                        'distance_from_previous': wp.get('distance_from_prev_km', 0),
                        'order': wp.get('order', 0)
                    })
                
                zones_data.append({
                    'zone_id': zone.get('zone_id'),
                    'zone_name': zone.get('zone_name'),
                    'zone_color': zone.get('zone_color'),
                    'depot': zone.get('depot'),
                    'waypoints': transformed_waypoints,
                    'path_coordinates': zone.get('path_coordinates', []),
                    'summary': zone.get('summary', {})
                })
            
            return jsonify({
                'zones': zones_data,
                'summary': result.get('summary', {}),
                'target_time': target_time
            })
        else:
            return jsonify({
                'zones': [],
                'summary': {
                    'total_zones': 0,
                    'total_bins': 0,
                    'total_distance_km': 0,
                    'total_duration_min': 0
                },
                'message': 'No bins need collection at this time'
            })
    except Exception as e:
        print(f"ERROR in zone route optimization: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# ADMIN API PROXY (Forward to FastAPI Backend)
# =============================================================================

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Proxy admin login to FastAPI backend."""
    try:
        from flask import request
        resp = requests.post(
            f"{BACKEND_URL}/admin/login",
            json=request.get_json(),
            timeout=5
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'detail': f'Backend connection error: {str(e)}'}), 503


@app.route('/api/admin/setup', methods=['POST'])
def admin_setup():
    """Proxy admin setup to FastAPI backend."""
    try:
        from flask import request
        password = request.args.get('password')
        resp = requests.post(
            f"{BACKEND_URL}/admin/setup?password={password}",
            timeout=5
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'detail': f'Backend connection error: {str(e)}'}), 503


@app.route('/api/admin/bins/<bin_id>', methods=['DELETE'])
def admin_delete_bin(bin_id):
    """Proxy bin deletion to FastAPI backend."""
    try:
        from flask import request
        auth_header = request.headers.get('Authorization')
        headers = {'Authorization': auth_header} if auth_header else {}
        resp = requests.delete(
            f"{BACKEND_URL}/admin/bins/{bin_id}",
            headers=headers,
            timeout=5
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'detail': f'Backend connection error: {str(e)}'}), 503


@app.route('/api/districts')
def get_districts():
    """Proxy districts endpoint to FastAPI backend."""
    try:
        resp = requests.get(f"{BACKEND_URL}/districts", timeout=5)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'detail': f'Backend connection error: {str(e)}'}), 503


@app.route('/api/bins/latest')
def get_bins_latest():
    """Proxy bins/latest endpoint to FastAPI backend."""
    try:
        resp = requests.get(f"{BACKEND_URL}/bins/latest", timeout=5)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'detail': f'Backend connection error: {str(e)}'}), 503


# =============================================================================
# COLLECTION DAY WORKFLOW PROXY
# =============================================================================

@app.route('/api/admin/collection/start', methods=['POST'])
def collection_start():
    """Proxy collection start to FastAPI backend."""
    try:
        from flask import request
        auth_header = request.headers.get('Authorization')
        headers = {'Authorization': auth_header} if auth_header else {}
        resp = requests.post(
            f"{BACKEND_URL}/admin/collection/start",
            json=request.get_json(),
            headers=headers,
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'detail': f'Backend connection error: {str(e)}'}), 503


@app.route('/api/admin/collection/check', methods=['POST'])
def collection_check():
    """Proxy collection check to FastAPI backend."""
    try:
        from flask import request
        auth_header = request.headers.get('Authorization')
        headers = {'Authorization': auth_header} if auth_header else {}
        resp = requests.post(
            f"{BACKEND_URL}/admin/collection/check",
            json=request.get_json(),
            headers=headers,
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'detail': f'Backend connection error: {str(e)}'}), 503


@app.route('/api/admin/collection/finish', methods=['POST'])
def collection_finish():
    """Proxy collection finish to FastAPI backend."""
    try:
        from flask import request
        auth_header = request.headers.get('Authorization')
        headers = {'Authorization': auth_header} if auth_header else {}
        resp = requests.post(
            f"{BACKEND_URL}/admin/collection/finish",
            json=request.get_json(),
            headers=headers,
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'detail': f'Backend connection error: {str(e)}'}), 503


@app.route('/api/admin/collection/end', methods=['POST'])
def collection_end():
    """Proxy collection end to FastAPI backend."""
    try:
        from flask import request
        auth_header = request.headers.get('Authorization')
        headers = {'Authorization': auth_header} if auth_header else {}
        resp = requests.post(
            f"{BACKEND_URL}/admin/collection/end",
            json=request.get_json(),
            headers=headers,
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'detail': f'Backend connection error: {str(e)}'}), 503


@app.route('/api/admin/collection/status/<zone_id>')
def collection_status(zone_id):
    """Proxy collection status to FastAPI backend."""
    try:
        from flask import request
        auth_header = request.headers.get('Authorization')
        headers = {'Authorization': auth_header} if auth_header else {}
        resp = requests.get(
            f"{BACKEND_URL}/admin/collection/status/{zone_id}",
            headers=headers,
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'detail': f'Backend connection error: {str(e)}'}), 503


if __name__ == '__main__':
    print("🚀 Starting CleanRoute Frontend...")
    print("📍 Dashboard: http://localhost:5001")
    print(f"🔗 Backend: {BACKEND_URL} ({'enabled' if USE_BACKEND else 'disabled'})")
    print(f"📂 CSV fallback: {MOCK_DATA_PATH}")
    app.run(host='0.0.0.0', port=5001, debug=True)
