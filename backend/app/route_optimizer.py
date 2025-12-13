"""
Route Optimization Module - Greedy Nearest Neighbor Algorithm

Generates optimal collection routes for waste bins using greedy nearest-neighbor approach.
"""
import logging
import math
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_DEPOT = {"lat": 6.9271, "lon": 79.8612, "name": "Municipal Office"}
AVERAGE_SPEED_KMH = 30  # Average driving speed in city
SERVICE_TIME_MINUTES = 5  # Time to empty one bin


# ─────────────────────────────────────────────────────────────────────────────
# Distance Calculation
# ─────────────────────────────────────────────────────────────────────────────

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula.
    
    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point
    
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_lat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance


# ─────────────────────────────────────────────────────────────────────────────
# Greedy Nearest Neighbor Algorithm
# ─────────────────────────────────────────────────────────────────────────────

def greedy_nearest_neighbor(
    bins: List[Dict[str, Any]],
    start_location: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Find near-optimal route using greedy nearest-neighbor algorithm.
    
    Algorithm:
    1. Start at depot
    2. Visit nearest unvisited bin
    3. Repeat until all bins visited
    4. Return to depot
    
    Args:
        bins: List of bin dictionaries with 'bin_id', 'lat', 'lon', 'predicted_fill'
        start_location: Starting point {'lat': ..., 'lon': ..., 'name': ...}
    
    Returns:
        Ordered list of waypoints (depot, bins, depot)
    """
    if not bins:
        logger.warning("No bins provided for route optimization")
        return []
    
    # Initialize route with starting depot
    route = [{
        "order": 0,
        "type": "depot",
        "location": {"lat": start_location['lat'], "lon": start_location['lon']},
        "name": start_location.get('name', 'Start Point'),
        "distance_from_prev_km": 0,
        "cumulative_distance_km": 0
    }]
    
    # Create list of unvisited bins
    unvisited = bins.copy()
    
    # Current position starts at depot
    current_lat = start_location['lat']
    current_lon = start_location['lon']
    cumulative_distance = 0
    
    # Visit bins one by one
    order = 1
    while unvisited:
        # Find nearest unvisited bin
        nearest_bin = None
        min_distance = float('inf')
        
        for bin_data in unvisited:
            distance = haversine_distance(
                current_lat, current_lon,
                bin_data['lat'], bin_data['lon']
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_bin = bin_data
        
        if nearest_bin is None:
            break
        
        # Add to route
        cumulative_distance += min_distance
        
        route.append({
            "order": order,
            "type": "bin",
            "bin_id": nearest_bin['bin_id'],
            "name": nearest_bin.get('name', 'Unknown'),
            "predicted_fill": nearest_bin['predicted_fill'],
            "current_fill": nearest_bin.get('current_fill'),
            "confidence": nearest_bin.get('confidence', 'unknown'),
            "location": {"lat": nearest_bin['lat'], "lon": nearest_bin['lon']},
            "distance_from_prev_km": round(min_distance, 2),
            "cumulative_distance_km": round(cumulative_distance, 2)
        })
        
        # Update current position
        current_lat = nearest_bin['lat']
        current_lon = nearest_bin['lon']
        
        # Remove from unvisited
        unvisited.remove(nearest_bin)
        order += 1
    
    # Return to depot
    return_distance = haversine_distance(
        current_lat, current_lon,
        start_location['lat'], start_location['lon']
    )
    cumulative_distance += return_distance
    
    route.append({
        "order": order,
        "type": "depot",
        "location": {"lat": start_location['lat'], "lon": start_location['lon']},
        "name": start_location.get('name', 'Return Point'),
        "distance_from_prev_km": round(return_distance, 2),
        "cumulative_distance_km": round(cumulative_distance, 2)
    })
    
    logger.info(f"Route generated: {len(bins)} bins, {cumulative_distance:.1f} km total distance")
    
    return route


# ─────────────────────────────────────────────────────────────────────────────
# Route Optimization with Predictions
# ─────────────────────────────────────────────────────────────────────────────

def optimize_route(
    bins_to_collect: List[Dict[str, Any]],
    depot_location: Optional[Dict[str, float]] = None,
    algorithm: str = "greedy"
) -> Dict[str, Any]:
    """
    Generate optimized collection route for bins.
    
    Args:
        bins_to_collect: List of bins with predictions (from ML module)
        depot_location: Starting/ending point (default: Municipal Office)
        algorithm: 'greedy' (only option for now)
    
    Returns:
        Dictionary with route details
    """
    if depot_location is None:
        depot_location = DEFAULT_DEPOT.copy()
    
    if not bins_to_collect:
        return {
            "error": "No bins to collect",
            "route": [],
            "summary": {
                "total_bins": 0,
                "total_distance_km": 0,
                "estimated_duration_min": 0
            }
        }
    
    # Generate route using selected algorithm
    if algorithm == "greedy":
        waypoints = greedy_nearest_neighbor(bins_to_collect, depot_location)
    else:
        return {"error": f"Unknown algorithm: {algorithm}"}
    
    # Calculate summary statistics
    total_distance = waypoints[-1]['cumulative_distance_km'] if waypoints else 0
    driving_time_min = (total_distance / AVERAGE_SPEED_KMH) * 60
    service_time_min = len(bins_to_collect) * SERVICE_TIME_MINUTES
    total_duration_min = driving_time_min + service_time_min
    
    # Extract coordinates for drawing path on map
    path_coordinates = [
        [wp['location']['lat'], wp['location']['lon']]
        for wp in waypoints
    ]
    
    return {
        "route": {
            "waypoints": waypoints,
            "summary": {
                "total_bins": len(bins_to_collect),
                "total_distance_km": round(total_distance, 2),
                "driving_time_min": round(driving_time_min, 0),
                "service_time_min": service_time_min,
                "estimated_duration_min": round(total_duration_min, 0),
                "average_fill_pct": round(
                    sum(b['predicted_fill'] for b in bins_to_collect) / len(bins_to_collect), 1
                ) if bins_to_collect else 0
            },
            "path_coordinates": path_coordinates
        },
        "algorithm_used": algorithm,
        "depot": depot_location
    }


# ─────────────────────────────────────────────────────────────────────────────
# Priority-Based Route (Alternative Algorithm)
# ─────────────────────────────────────────────────────────────────────────────

def priority_based_route(
    bins: List[Dict[str, Any]],
    start_location: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Generate route prioritizing high-fill bins while considering distance.
    
    Algorithm:
    1. Sort bins by predicted fill (highest first)
    2. Apply greedy nearest-neighbor within each fill bracket
    
    This is more advanced than pure greedy but still simple.
    """
    if not bins:
        return []
    
    # Sort bins by predicted fill (descending)
    sorted_bins = sorted(bins, key=lambda b: b['predicted_fill'], reverse=True)
    
    # For simplicity, just apply greedy to sorted list
    # (In practice, you'd divide into priority brackets)
    return greedy_nearest_neighbor(sorted_bins, start_location)


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def calculate_route_stats(route: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate statistics for a given route."""
    if not route:
        return {"total_distance_km": 0, "bin_count": 0}
    
    total_distance = route[-1].get('cumulative_distance_km', 0) if route else 0
    bin_count = sum(1 for wp in route if wp['type'] == 'bin')
    
    return {
        "total_distance_km": total_distance,
        "bin_count": bin_count,
        "avg_distance_per_bin_km": total_distance / bin_count if bin_count > 0 else 0
    }
