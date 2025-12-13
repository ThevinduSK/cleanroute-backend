// CleanRoute Frontend Application
let map;
let markers = {};
let routeLine = null;
let allBins = [];
let currentPredictions = null;

// Initialize map when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    loadStats();
    loadBins();
    setupDefaultDate();
    
    // Auto-refresh stats every 30 seconds
    setInterval(loadStats, 30000);
});

// Initialize Leaflet map
function initializeMap() {
    // Center on Colombo, Sri Lanka
    map = L.map('map', {
        zoomControl: true,
        attributionControl: false
    }).setView([6.9271, 79.8612], 12);

    // Dark theme tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd'
    }).addTo(map);

    // Add attribution
    L.control.attribution({
        position: 'bottomright',
        prefix: 'CleanRoute'
    }).addTo(map);
}

// Set default date to tomorrow
function setupDefaultDate() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateStr = tomorrow.toISOString().split('T')[0];
    document.getElementById('predictionDate').value = dateStr;
}

// Load system statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('totalBins').textContent = stats.total_bins;
        document.getElementById('activeBins').textContent = stats.active_bins;
        document.getElementById('warningBins').textContent = stats.warning_bins;
        document.getElementById('fullBins').textContent = stats.full_bins;
        document.getElementById('avgFill').textContent = stats.average_fill_level + '%';
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load all bins and display on map
async function loadBins() {
    try {
        const response = await fetch('/api/bins');
        allBins = await response.json();
        
        // Clear existing markers
        Object.values(markers).forEach(marker => map.removeLayer(marker));
        markers = {};
        
        // Add markers for each bin
        allBins.forEach(bin => {
            addBinMarker(bin);
        });
        
    } catch (error) {
        console.error('Error loading bins:', error);
        showNotification('Failed to load bins', 'error');
    }
}

// Add bin marker to map
function addBinMarker(bin) {
    const fillLevel = bin.current_fill_level || 0;
    const color = getBinColor(fillLevel, bin.status);
    
    // Create custom icon
    const icon = L.divIcon({
        className: 'custom-marker',
        html: `
            <div style="
                width: 30px;
                height: 30px;
                background: ${color};
                border: 3px solid rgba(255,255,255,0.5);
                border-radius: 50%;
                box-shadow: 0 0 15px ${color};
                position: relative;
                cursor: pointer;
            ">
                <div style="
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: #000;
                    font-weight: bold;
                    font-size: 12px;
                ">${Math.round(fillLevel)}%</div>
            </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });
    
    const marker = L.marker([bin.latitude, bin.longitude], { icon: icon })
        .addTo(map);
    
    // Create popup content
    const popupContent = createPopupContent(bin);
    marker.bindPopup(popupContent);
    
    // Store marker reference
    markers[bin.bin_id] = marker;
}

// Get bin color based on fill level and status
function getBinColor(fillLevel, status) {
    if (status !== 'active') {
        return '#666666';
    }
    if (fillLevel >= 90) {
        return '#ff0055'; // Critical - red
    } else if (fillLevel >= 70) {
        return '#ffaa00'; // Warning - orange
    } else {
        return '#00ff88'; // Normal - green
    }
}

// Create popup content for bin
function createPopupContent(bin) {
    const fillLevel = bin.current_fill_level || 0;
    const battery = bin.battery_level || 0;
    const status = bin.status || 'unknown';
    
    return `
        <div class="popup-content">
            <div class="popup-title">${bin.location}</div>
            <div class="popup-info">
                <span class="popup-label">Bin ID:</span>
                <span class="popup-value">${bin.bin_id}</span>
            </div>
            <div class="popup-info">
                <span class="popup-label">Fill Level:</span>
                <span class="popup-value">${Math.round(fillLevel)}%</span>
            </div>
            <div class="popup-info">
                <span class="popup-label">Battery:</span>
                <span class="popup-value">${Math.round(battery)}%</span>
            </div>
            <div class="popup-info">
                <span class="popup-label">Status:</span>
                <span class="popup-value" style="text-transform: capitalize;">${status}</span>
            </div>
            <div class="popup-info">
                <span class="popup-label">Capacity:</span>
                <span class="popup-value">${bin.capacity_liters}L</span>
            </div>
            <button class="popup-btn" onclick="showBinDetails('${bin.bin_id}')">
                View Details
            </button>
        </div>
    `;
}

// Run ML prediction
async function runPrediction() {
    const dateInput = document.getElementById('predictionDate').value;
    const timeInput = document.getElementById('predictionTime').value;
    
    if (!dateInput || !timeInput) {
        showNotification('Please select date and time', 'error');
        return;
    }
    
    // Format: YYYY-MM-DD-HH-MM
    const targetTime = `${dateInput}-${timeInput.replace(':', '-')}`;
    
    showLoading(true);
    
    try {
        const response = await fetch(`/api/predictions/${targetTime}`);
        currentPredictions = await response.json();
        
        // Update markers with predictions
        currentPredictions.forEach(pred => {
            updateBinMarkerWithPrediction(pred);
        });
        
        const needsCollection = currentPredictions.filter(p => p.needs_collection).length;
        const willOverflow = currentPredictions.filter(p => p.will_overflow).length;
        
        showNotification(
            `Prediction complete: ${needsCollection} bins need collection, ${willOverflow} may overflow`,
            'success'
        );
        
    } catch (error) {
        console.error('Error running prediction:', error);
        showNotification('Prediction failed', 'error');
    } finally {
        showLoading(false);
    }
}

// Update bin marker with prediction
function updateBinMarkerWithPrediction(prediction) {
    const marker = markers[prediction.bin_id];
    if (!marker) return;
    
    const fillLevel = prediction.predicted_fill_level;
    const color = getBinColor(fillLevel, 'active');
    
    // Update icon
    const icon = L.divIcon({
        className: 'custom-marker',
        html: `
            <div style="
                width: 35px;
                height: 35px;
                background: ${color};
                border: 3px solid rgba(255,255,255,0.8);
                border-radius: 50%;
                box-shadow: 0 0 20px ${color};
                position: relative;
                cursor: pointer;
                animation: pulse 2s infinite;
            ">
                <div style="
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: #000;
                    font-weight: bold;
                    font-size: 11px;
                ">${Math.round(fillLevel)}%</div>
            </div>
        `,
        iconSize: [35, 35],
        iconAnchor: [17, 17]
    });
    
    marker.setIcon(icon);
    
    // Update popup
    const popupContent = `
        <div class="popup-content">
            <div class="popup-title">${prediction.location}</div>
            <div class="popup-info">
                <span class="popup-label">Predicted Fill:</span>
                <span class="popup-value">${Math.round(fillLevel)}%</span>
            </div>
            <div class="popup-info">
                <span class="popup-label">Status:</span>
                <span class="popup-value">${prediction.will_overflow ? '⚠️ Will Overflow' : 
                    prediction.needs_collection ? '⚠️ Needs Collection' : '✓ Normal'}</span>
            </div>
            <div class="popup-info">
                <span class="popup-label">Confidence:</span>
                <span class="popup-value" style="text-transform: capitalize;">${prediction.confidence}</span>
            </div>
            <button class="popup-btn" onclick="showBinDetails('${prediction.bin_id}')">
                View Details
            </button>
        </div>
    `;
    
    marker.setPopupContent(popupContent);
}

// Optimize collection route
async function optimizeRoute() {
    const dateInput = document.getElementById('predictionDate').value;
    const timeInput = document.getElementById('predictionTime').value;
    
    if (!dateInput || !timeInput) {
        showNotification('Please select date and time', 'error');
        return;
    }
    
    const targetTime = `${dateInput}-${timeInput.replace(':', '-')}`;
    
    showLoading(true);
    
    try {
        const response = await fetch(`/api/route/${targetTime}`);
        const route = await response.json();
        
        if (route.bins_count === 0) {
            showNotification('No bins need collection at this time', 'info');
            document.getElementById('routeInfo').style.display = 'none';
            return;
        }
        
        // Display route on map
        displayRoute(route);
        
        // Show route info panel
        displayRouteInfo(route);
        
        showNotification(`Route optimized: ${route.bins_count} bins, ${route.total_distance_km.toFixed(1)} km`, 'success');
        
    } catch (error) {
        console.error('Error optimizing route:', error);
        showNotification('Route optimization failed', 'error');
    } finally {
        showLoading(false);
    }
}

// Display route on map
function displayRoute(route) {
    // Remove existing route
    if (routeLine) {
        map.removeLayer(routeLine);
    }
    
    // Create route line
    const waypoints = route.waypoints.map(wp => [wp.latitude, wp.longitude]);
    
    routeLine = L.polyline(waypoints, {
        color: '#00ff88',
        weight: 4,
        opacity: 0.8,
        dashArray: '10, 10',
        lineJoin: 'round'
    }).addTo(map);
    
    // Add route markers with numbers
    route.waypoints.forEach((wp, index) => {
        if (wp.type === 'bin') {
            const numberIcon = L.divIcon({
                className: 'route-number-marker',
                html: `
                    <div style="
                        width: 30px;
                        height: 30px;
                        background: #00ff88;
                        border: 3px solid #fff;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        font-size: 14px;
                        color: #000;
                        box-shadow: 0 0 20px #00ff88;
                    ">${index}</div>
                `,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });
            
            L.marker([wp.latitude, wp.longitude], { icon: numberIcon })
                .addTo(map)
                .bindPopup(`
                    <div class="popup-content">
                        <div class="popup-title">Stop ${index}: ${wp.location}</div>
                        <div class="popup-info">
                            <span class="popup-label">Predicted Fill:</span>
                            <span class="popup-value">${Math.round(wp.predicted_fill_level)}%</span>
                        </div>
                    </div>
                `);
        }
    });
    
    // Fit map to route bounds
    map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });
}

// Display route information panel
function displayRouteInfo(route) {
    document.getElementById('routeBinsCount').textContent = route.bins_count;
    document.getElementById('routeDistance').textContent = route.total_distance_km.toFixed(1) + ' km';
    document.getElementById('routeTime').textContent = route.estimated_time_hours.toFixed(1) + ' hrs';
    
    // Display waypoints
    const waypointsHtml = route.waypoints
        .filter(wp => wp.type === 'bin')
        .map((wp, index) => `
            <div class="waypoint-item">
                <span class="waypoint-number">${index}</span>
                <div>
                    <div class="waypoint-location">${wp.location}</div>
                    <div class="waypoint-fill">Fill: ${Math.round(wp.predicted_fill_level)}% | 
                        ${wp.distance_from_previous ? wp.distance_from_previous.toFixed(1) + ' km' : 'Start'}</div>
                </div>
            </div>
        `).join('');
    
    document.getElementById('routeWaypoints').innerHTML = waypointsHtml;
    document.getElementById('routeInfo').style.display = 'block';
}

// Reset view to default
function resetView() {
    // Remove route
    if (routeLine) {
        map.removeLayer(routeLine);
        routeLine = null;
    }
    
    // Remove route markers
    map.eachLayer(layer => {
        if (layer instanceof L.Marker && layer.options.icon && 
            layer.options.icon.options.className === 'route-number-marker') {
            map.removeLayer(layer);
        }
    });
    
    // Reload bins
    loadBins();
    
    // Hide route info
    document.getElementById('routeInfo').style.display = 'none';
    
    // Reset view
    map.setView([6.9271, 79.8612], 12);
    
    showNotification('View reset', 'info');
}

// Show bin details in modal
async function showBinDetails(binId) {
    showLoading(true);
    
    try {
        // Get bin info
        const bin = allBins.find(b => b.bin_id === binId);
        
        // Get history
        const response = await fetch(`/api/bins/${binId}/history`);
        const history = await response.json();
        
        // Build modal content
        const modalBody = document.getElementById('modalBody');
        modalBody.innerHTML = `
            <div class="bin-detail-grid">
                <div class="detail-card">
                    <div class="detail-label">Current Fill Level</div>
                    <div class="detail-value">${Math.round(bin.current_fill_level)}%</div>
                </div>
                <div class="detail-card">
                    <div class="detail-label">Battery Level</div>
                    <div class="detail-value">${Math.round(bin.battery_level)}%</div>
                </div>
                <div class="detail-card">
                    <div class="detail-label">Capacity</div>
                    <div class="detail-value">${bin.capacity_liters}L</div>
                </div>
                <div class="detail-card">
                    <div class="detail-label">Status</div>
                    <div class="detail-value" style="font-size: 18px; text-transform: capitalize;">${bin.status}</div>
                </div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">Fill Level History (Last 30 Days)</div>
                <canvas id="historyChart"></canvas>
            </div>
        `;
        
        document.getElementById('modalTitle').textContent = `${bin.location} (${binId})`;
        document.getElementById('binModal').classList.add('active');
        
        // Draw chart
        setTimeout(() => drawHistoryChart(history), 100);
        
    } catch (error) {
        console.error('Error loading bin details:', error);
        showNotification('Failed to load bin details', 'error');
    } finally {
        showLoading(false);
    }
}

// Draw history chart
function drawHistoryChart(history) {
    const ctx = document.getElementById('historyChart').getContext('2d');
    
    // Prepare data
    const labels = history.map(h => {
        const date = new Date(h.timestamp);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    });
    
    const fillData = history.map(h => h.fill_level);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Fill Level (%)',
                data: fillData,
                borderColor: '#00ffff',
                backgroundColor: 'rgba(0, 255, 255, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#a0a0b0',
                        font: {
                            family: 'Rajdhani',
                            size: 14
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#a0a0b0',
                        maxRotation: 45,
                        minRotation: 45,
                        font: {
                            family: 'Rajdhani',
                            size: 11
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: '#a0a0b0',
                        font: {
                            family: 'Rajdhani',
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// Close modal
function closeModal() {
    document.getElementById('binModal').classList.remove('active');
}

// Show/hide loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Simple console log for now - you can enhance this with a toast library
    const emoji = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    };
    
    console.log(`${emoji[type]} ${message}`);
    
    // You could add a toast notification library here for better UX
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('binModal');
    if (event.target === modal) {
        closeModal();
    }
});
