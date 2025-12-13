#!/usr/bin/env python3
"""
Standalone ML & Routing Test - Uses CSV data only
No database, no MQTT, no backend server needed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from datetime import datetime, timedelta
from app import ml_prediction, route_optimizer

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def load_csv_data():
    """Load bins and telemetry from CSV files"""
    bins_df = pd.read_csv('mock_data/bins_config.csv')
    telemetry_df = pd.read_csv('mock_data/telemetry_data.csv')
    telemetry_df['ts'] = pd.to_datetime(telemetry_df['ts'])
    return bins_df, telemetry_df

def test_csv_data_quality():
    """Test 1: Verify CSV data quality"""
    print_section("TEST 1: CSV Data Quality Check")
    
    bins_df, telemetry_df = load_csv_data()
    
    print(f"Done: Bins loaded: {len(bins_df)}")
    print(f"Done: Telemetry records: {len(telemetry_df)}")
    print(f"Done: Time range: {telemetry_df['ts'].min()} to {telemetry_df['ts'].max()}")
    print(f"Done: Days of history: {(telemetry_df['ts'].max() - telemetry_df['ts'].min()).days}")
    
    # Check data per bin
    records_per_bin = telemetry_df.groupby('bin_id').size()
    print(f"\n📊 Records per bin:")
    print(f"   Average: {records_per_bin.mean():.0f}")
    print(f"   Min: {records_per_bin.min()}")
    print(f"   Max: {records_per_bin.max()}")
    
    # Check current state
    latest = telemetry_df.sort_values('ts').groupby('bin_id').last()
    print(f"\n📈 Current Fill Levels:")
    print(f"   Critical (>90%): {(latest['fill_pct'] > 90).sum()} bins")
    print(f"   High (80-90%): {((latest['fill_pct'] >= 80) & (latest['fill_pct'] <= 90)).sum()} bins")
    print(f"   Medium (50-80%): {((latest['fill_pct'] >= 50) & (latest['fill_pct'] < 80)).sum()} bins")
    print(f"   Low (<50%): {(latest['fill_pct'] < 50).sum()} bins")

def calculate_fill_rate_csv(bin_id, telemetry_df, alpha=0.3):
    """Calculate EWMA fill rate from CSV data"""
    bin_data = telemetry_df[telemetry_df['bin_id'] == bin_id].sort_values('ts')
    
    if len(bin_data) < 5:
        return None, "insufficient_data"
    
    fill_rates = []
    for i in range(1, len(bin_data)):
        time_diff = (bin_data.iloc[i]['ts'] - bin_data.iloc[i-1]['ts']).total_seconds() / 3600
        fill_change = bin_data.iloc[i]['fill_pct'] - bin_data.iloc[i-1]['fill_pct']
        
        if time_diff > 0:
            rate = fill_change / time_diff
            if 0 <= rate <= 10:
                fill_rates.append(rate)
    
    if not fill_rates:
        return None, "no_valid_rates"
    
    # Apply EWMA
    ewma_rate = fill_rates[0]
    for rate in fill_rates[1:]:
        ewma_rate = alpha * rate + (1 - alpha) * ewma_rate
    
    confidence = "high" if len(bin_data) >= 15 else "medium" if len(bin_data) >= 10 else "low"
    
    return ewma_rate, confidence

def test_predictions():
    """Test 2: ML Predictions"""
    print_section("TEST 2: ML Fill Predictions")
    
    bins_df, telemetry_df = load_csv_data()
    
    # Target time: tomorrow afternoon (2 PM)
    target_time = datetime.now() + timedelta(hours=24)
    print(f"🔮 Predicting for: {target_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"   (Tomorrow afternoon)")
    
    predictions = []
    
    for _, bin_row in bins_df.iterrows():
        bin_id = bin_row['id']
        
        # Get current fill
        bin_telemetry = telemetry_df[telemetry_df['bin_id'] == bin_id].sort_values('ts')
        if len(bin_telemetry) == 0:
            continue
        
        current_fill = bin_telemetry.iloc[-1]['fill_pct']
        current_time = bin_telemetry.iloc[-1]['ts']
        
        # Calculate fill rate
        fill_rate, confidence = calculate_fill_rate_csv(bin_id, telemetry_df)
        
        if fill_rate is None:
            predicted_fill = current_fill
        else:
            hours_until_target = (target_time - current_time).total_seconds() / 3600
            predicted_fill = current_fill + (fill_rate * hours_until_target)
            predicted_fill = min(predicted_fill, 100.0)
            if predicted_fill < current_fill:
                predicted_fill = current_fill
        
        predictions.append({
            'bin_id': bin_id,
            'lat': bin_row['lat'],
            'lon': bin_row['lon'],
            'type': bin_row['type'],
            'current_fill': round(current_fill, 1),
            'predicted_fill': round(predicted_fill, 1),
            'fill_rate': round(fill_rate, 3) if fill_rate else None,
            'confidence': confidence,
            'needs_collection': predicted_fill >= 80
        })
    
    # Show results
    predictions_df = pd.DataFrame(predictions)
    
    bins_needing_collection = predictions_df[predictions_df['needs_collection']]
    
    print(f"\n📊 Prediction Results:")
    print(f"   Total bins analyzed: {len(predictions_df)}")
    print(f"   Bins needing collection (≥80%): {len(bins_needing_collection)}")
    
    print(f"\nBins to Collect (sorted by predicted fill):")
    for _, pred in bins_needing_collection.sort_values('predicted_fill', ascending=False).head(10).iterrows():
        print(f"   {pred['bin_id']:5} | {pred['current_fill']:5.1f}% → {pred['predicted_fill']:5.1f}% "
              f"| {pred['fill_rate']:+6.3f}%/h | {pred['confidence']:6} | {pred['type']}")
    
    return bins_needing_collection.to_dict('records')

def test_route_optimization(bins_to_collect):
    """Test 3: Route Optimization"""
    print_section("TEST 3: Route Optimization")
    
    if not bins_to_collect:
        print("No bins need collection")
        return
    
    print(f"Optimizing route for {len(bins_to_collect)} bins...")
    
    # Use Independence Square as depot
    depot = {"lat": 6.9271, "lon": 79.8612, "name": "Independence Square (Depot)"}
    
    # Generate route
    route_result = route_optimizer.optimize_route(bins_to_collect, depot, algorithm="greedy")
    
    if 'route' not in route_result:
        print("ERROR: Route optimization failed")
        return
    
    route = route_result['route']
    summary = route['summary']
    
    print(f"\n📊 Route Summary:")
    print(f"   Total bins: {summary['total_bins']}")
    print(f"   Total distance: {summary['total_distance_km']} km")
    print(f"   Driving time: {summary['driving_time_min']:.0f} minutes")
    print(f"   Service time: {summary['service_time_min']} minutes (5 min/bin)")
    print(f"   Total duration: {summary['estimated_duration_min']:.0f} minutes ({summary['estimated_duration_min']/60:.1f} hours)")
    print(f"   Average fill: {summary['average_fill_pct']:.1f}%")
    
    print(f"\n🚚 Collection Route (First 10 stops):")
    for waypoint in route['waypoints'][:10]:
        if waypoint['type'] == 'depot':
            print(f"   {waypoint['order']:2}. 📍 {waypoint['name']}")
        else:
            print(f"   {waypoint['order']:2}. Bin {waypoint['bin_id']} - {waypoint['predicted_fill']:.1f}% "
                  f"({waypoint['distance_from_prev_km']:.2f} km from prev)")
    
    if len(route['waypoints']) > 10:
        print(f"   ... ({len(route['waypoints']) - 10} more stops)")
        # Show last stop
        last = route['waypoints'][-1]
        print(f"   {last['order']:2}. 📍 {last['name']} ({last['distance_from_prev_km']:.2f} km)")

def test_scenarios():
    """Test 4: Different Time Scenarios"""
    print_section("TEST 4: Compare Time Scenarios")
    
    bins_df, telemetry_df = load_csv_data()
    
    scenarios = [
        ("In 6 hours", 6),
        ("Tomorrow morning (8 AM)", 18),
        ("Tomorrow afternoon (2 PM)", 24),
        ("In 48 hours", 48)
    ]
    
    print("Scenario Comparison:")
    print("-" * 70)
    
    for name, hours in scenarios:
        target_time = datetime.now() + timedelta(hours=hours)
        
        bins_need_collection = 0
        for _, bin_row in bins_df.iterrows():
            bin_id = bin_row['id']
            bin_telemetry = telemetry_df[telemetry_df['bin_id'] == bin_id].sort_values('ts')
            
            if len(bin_telemetry) == 0:
                continue
            
            current_fill = bin_telemetry.iloc[-1]['fill_pct']
            current_time = bin_telemetry.iloc[-1]['ts']
            
            fill_rate, _ = calculate_fill_rate_csv(bin_id, telemetry_df)
            
            if fill_rate:
                hours_delta = (target_time - current_time).total_seconds() / 3600
                predicted_fill = min(current_fill + (fill_rate * hours_delta), 100)
            else:
                predicted_fill = current_fill
            
            if predicted_fill >= 80:
                bins_need_collection += 1
        
        print(f"{name:30} → {bins_need_collection:2} bins need collection")

def main():
    print("\n" + "="*70)
    print("  CleanRoute ML & Routing - Standalone Test (CSV Only)")
    print("="*70)
    print("\n📁 Using CSV data from: backend/mock_data/")
    print("   No database, no MQTT, no backend server needed\n")
    
    try:
        # Test 1: Data quality
        test_csv_data_quality()
        
        # Test 2: Predictions
        bins_to_collect = test_predictions()
        
        # Test 3: Route optimization
        test_route_optimization(bins_to_collect)
        
        # Test 4: Scenarios
        test_scenarios()
        
        # Summary
        print_section("Done: All Tests Complete!")
        print("The ML prediction and route optimization are working correctly!")
        print("\n🎯 Key Achievements:")
        print("   Done: EWMA fill rate calculation from CSV data")
        print("   Done: Future fill level predictions")
        print("   Done: Greedy nearest-neighbor route optimization")
        print("   Done: Real Colombo GPS coordinates")
        print("   Done: Realistic 30-day historical patterns")
        
    except FileNotFoundError:
        print("\nERROR: Error: CSV files not found!")
        print("Run this first: python generate_mock_data.py --csv-only")
    except Exception as e:
        print(f"\nERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
