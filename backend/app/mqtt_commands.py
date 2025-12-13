"""
MQTT Command Service - Downlink Commands to Bins
Sends commands FROM backend TO devices.

Command Topics:
- cleanroute/bins/{bin_id}/command
- cleanroute/bins/broadcast/command (all bins)

Command Types:
- wake_up: Activate device and start hourly telemetry
- sleep: Put device to sleep mode
- reset_emptied: Reset the emptied flag
- get_status: Request immediate status update
- update_config: Send new configuration

Security: Supports TLS encryption and username/password authentication.
"""
import json
import logging
import ssl
import os
from datetime import datetime
from typing import Optional, Dict, Any

import paho.mqtt.client as mqtt

from . import config
from . import db

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Global MQTT Client for Commands
# ─────────────────────────────────────────────────────────────────────────────
command_client = None


def init_command_client():
    """
    Initialize a separate MQTT client for publishing commands.
    Supports TLS + authentication when MQTT_USE_TLS=true.
    """
    global command_client
    if command_client is None:
        command_client = mqtt.Client(client_id="cleanroute_command_publisher")
        
        # Determine connection mode
        if config.MQTT_USE_TLS:
            port = config.MQTT_TLS_PORT
            
            # Configure TLS
            ca_cert_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                config.MQTT_CA_CERT
            )
            
            if not os.path.exists(ca_cert_path):
                logger.error(f"CA certificate not found: {ca_cert_path}")
                raise FileNotFoundError(f"CA certificate not found: {ca_cert_path}")
            
            command_client.tls_set(
                ca_certs=ca_cert_path,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
            
            # Set username/password authentication
            command_client.username_pw_set(
                config.MQTT_USERNAME,
                config.MQTT_PASSWORD
            )
            
            logger.info(f"Command client TLS enabled")
        else:
            port = config.MQTT_PORT
            logger.info("WARNING: Command client running in insecure mode")
        
        try:
            command_client.connect(config.MQTT_BROKER, port, keepalive=60)
            command_client.loop_start()
            logger.info(f"Command publisher initialized on {config.MQTT_BROKER}:{port}")
        except Exception as e:
            logger.error(f"Failed to initialize command client: {e}")
            raise


def stop_command_client():
    """Stop the command client."""
    global command_client
    if command_client:
        command_client.loop_stop()
        command_client.disconnect()
        logger.info("Command publisher stopped")


# ─────────────────────────────────────────────────────────────────────────────
# Command Functions
# ─────────────────────────────────────────────────────────────────────────────

def send_command(
    bin_id: str,
    command_type: str,
    payload: Optional[Dict[str, Any]] = None,
    qos: int = 1,
    retain: bool = False
) -> bool:
    """
    Send a command to a specific bin.
    
    Args:
        bin_id: Target bin ID or "broadcast" for all bins
        command_type: Type of command (wake_up, sleep, etc.)
        payload: Additional command parameters
        qos: MQTT QoS level (0, 1, or 2)
        retain: Whether to retain the message
    
    Returns:
        True if command sent successfully
    """
    if command_client is None:
        init_command_client()
    
    topic = f"cleanroute/bins/{bin_id}/command"
    
    command_payload = {
        "command": command_type,
        "timestamp": datetime.utcnow().isoformat(),
        "params": payload or {}
    }
    
    try:
        result = command_client.publish(
            topic,
            json.dumps(command_payload),
            qos=qos,
            retain=retain
        )
        
        # Log command
        db.log_command(bin_id, command_type, command_payload)
        
        logger.info(f"Sent {command_type} to {bin_id} (QoS={qos})")
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    except Exception as e:
        logger.error(f"Failed to send command to {bin_id}: {e}")
        return False


def wake_up_bin(bin_id: str, collection_hours: int = 12) -> bool:
    """
    Send wake-up command to bin.
    Device should start sending telemetry hourly for specified hours.
    """
    payload = {
        "collection_hours": collection_hours,
        "telemetry_interval_minutes": 60
    }
    
    # Update database
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE bins SET last_wake_command = NOW(), sleep_mode = FALSE WHERE bin_id = %s",
            (bin_id,)
        )
    
    return send_command(bin_id, "wake_up", payload, qos=1)


def sleep_bin(bin_id: str) -> bool:
    """Send sleep command to bin. Device enters low-power mode."""
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE bins SET sleep_mode = TRUE WHERE bin_id = %s",
            (bin_id,)
        )
    
    return send_command(bin_id, "sleep", qos=1)


def reset_emptied_flag(bin_id: str) -> bool:
    """Reset the emptied flag on the device."""
    payload = {"emptied": False}
    return send_command(bin_id, "reset_emptied", payload, qos=1)


def request_status(bin_id: str) -> bool:
    """Request immediate status update from device."""
    return send_command(bin_id, "get_status", qos=1)


def update_device_config(
    bin_id: str,
    telemetry_interval: Optional[int] = None,
    battery_threshold: Optional[float] = None
) -> bool:
    """Send configuration update to device."""
    payload = {}
    if telemetry_interval:
        payload["telemetry_interval_minutes"] = telemetry_interval
    if battery_threshold:
        payload["battery_threshold_v"] = battery_threshold
    
    return send_command(bin_id, "update_config", payload, qos=1)


# ─────────────────────────────────────────────────────────────────────────────
# Broadcast Commands (All Bins)
# ─────────────────────────────────────────────────────────────────────────────

def broadcast_wake_up(collection_hours: int = 12) -> bool:
    """Wake up ALL bins for collection day."""
    payload = {
        "collection_hours": collection_hours,
        "telemetry_interval_minutes": 60
    }
    
    # Update all bins in database
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE bins SET last_wake_command = NOW(), sleep_mode = FALSE"
        )
    
    logger.info(f"Broadcasting wake_up to all bins")
    return send_command("broadcast", "wake_up", payload, qos=1)


def broadcast_sleep() -> bool:
    """Put all bins to sleep."""
    with db.get_cursor(commit=True) as cur:
        cur.execute("UPDATE bins SET sleep_mode = TRUE")
    
    logger.info(f"Broadcasting sleep to all bins")
    return send_command("broadcast", "sleep", qos=1)


# ─────────────────────────────────────────────────────────────────────────────
# Collection Day Workflow
# ─────────────────────────────────────────────────────────────────────────────

def start_collection_day(collection_hours: int = 12) -> Dict[str, Any]:
    """
    Start collection day workflow:
    1. Wake up all bins
    2. Create alerts to remind users
    3. Return status
    """
    success = broadcast_wake_up(collection_hours)
    
    # Get all bins with user info
    with db.get_cursor() as cur:
        cur.execute("""
            SELECT bin_id, user_name, user_phone 
            FROM bins 
            WHERE user_id IS NOT NULL
        """)
        bins = cur.fetchall()
    
    # Create reminder alerts for users
    for bin in bins:
        db.create_alert(
            bin_id=bin['bin_id'],
            alert_type="collection_reminder",
            severity="info",
            message=f"Collection day today! Please ensure your bin device is turned on. User: {bin['user_name']}"
        )
    
    return {
        "success": success,
        "bins_notified": len(bins),
        "collection_hours": collection_hours,
        "started_at": datetime.utcnow().isoformat()
    }


def end_collection_day() -> Dict[str, Any]:
    """
    End collection day workflow:
    1. Send sleep command to all bins
    2. Mark collection complete
    """
    success = broadcast_sleep()
    
    return {
        "success": success,
        "ended_at": datetime.utcnow().isoformat()
    }


# ─────────────────────────────────────────────────────────────────────────────
# Zone-Specific Commands
# ─────────────────────────────────────────────────────────────────────────────

def get_bins_in_zone(zone_id: str) -> list:
    """
    Get all bins within a specific zone based on their bin_id prefix.
    
    Zone to Prefix mapping for Colombo:
    - colombo_zone1: COL1xx (Fort & Pettah)
    - colombo_zone2: COL2xx (Kollupitiya)
    - colombo_zone3: COL3xx (Wellawatta/Dehiwala)
    - colombo_zone4: COL4xx (Nugegoda/Kotte)
    """
    # Map zone IDs to bin prefixes
    zone_prefix_map = {
        # Colombo zones
        "colombo_zone1": ["COL1"],
        "colombo_zone2": ["COL2"],
        "colombo_zone3": ["COL3"],
        "colombo_zone4": ["COL4"],
        # Legacy/other Colombo bins
        "colombo": ["COL", "B0"],
        # Other districts
        "kurunegala_zone1": ["KUR1"],
        "kurunegala_zone2": ["KUR2"],
        "kurunegala_zone3": ["KUR3"],
        "galle_zone1": ["GAL1"],
        "galle_zone2": ["GAL2"],
        "kandy_zone1": ["KAN1"],
        "kandy_zone2": ["KAN2"],
        "matara_zone1": ["MAT1"],
    }
    
    prefixes = zone_prefix_map.get(zone_id, [])
    if not prefixes:
        logger.warning(f"No prefix mapping found for zone: {zone_id}")
        return []
    
    bins = []
    with db.get_cursor() as cur:
        # Build query to match any of the prefixes
        conditions = " OR ".join([f"bin_id LIKE %s" for _ in prefixes])
        params = [f"{prefix}%" for prefix in prefixes]
        
        cur.execute(f"SELECT bin_id FROM bins WHERE {conditions}", params)
        bins = [row['bin_id'] for row in cur.fetchall()]
    
    return bins


def wake_up_zone(zone_id: str, zone_name: str = None) -> Dict[str, Any]:
    """
    Wake up all bins in a specific zone for collection.
    
    Args:
        zone_id: Zone identifier (e.g., "colombo_zone1")
        zone_name: Human-readable zone name for logging
    
    Returns:
        Status of the wake-up operation
    """
    bins = get_bins_in_zone(zone_id)
    
    if not bins:
        logger.warning(f"No bins found in zone {zone_id}")
        return {
            "success": False,
            "zone_id": zone_id,
            "zone_name": zone_name,
            "message": "No bins found in this zone",
            "bins_count": 0
        }
    
    # Send wake-up command to each bin in the zone
    success_count = 0
    failed_bins = []
    
    for bin_id in bins:
        try:
            if wake_up_bin(bin_id, collection_hours=12):
                success_count += 1
            else:
                failed_bins.append(bin_id)
        except Exception as e:
            logger.error(f"Failed to wake up {bin_id}: {e}")
            failed_bins.append(bin_id)
    
    # Also send a zone broadcast for any bins we might have missed
    zone_topic = f"cleanroute/zones/{zone_id}/command"
    payload = {
        "command": "wake_up",
        "zone_id": zone_id,
        "timestamp": datetime.utcnow().isoformat(),
        "params": {"collection_hours": 12}
    }
    
    try:
        if command_client is None:
            init_command_client()
        command_client.publish(zone_topic, json.dumps(payload), qos=1)
        logger.info(f"Broadcast wake_up to zone {zone_id}")
    except Exception as e:
        logger.error(f"Zone broadcast failed: {e}")
    
    return {
        "success": success_count > 0,
        "zone_id": zone_id,
        "zone_name": zone_name,
        "bins_awakened": success_count,
        "bins_failed": failed_bins,
        "total_bins": len(bins),
        "started_at": datetime.utcnow().isoformat()
    }


def sleep_zone(zone_id: str, zone_name: str = None) -> Dict[str, Any]:
    """
    Put all bins in a specific zone to sleep mode.
    
    Args:
        zone_id: Zone identifier (e.g., "colombo_zone1")
        zone_name: Human-readable zone name for logging
    
    Returns:
        Status of the sleep operation
    """
    bins = get_bins_in_zone(zone_id)
    
    if not bins:
        return {
            "success": False,
            "zone_id": zone_id,
            "zone_name": zone_name,
            "message": "No bins found in this zone",
            "bins_count": 0
        }
    
    # Send sleep command to each bin
    success_count = 0
    failed_bins = []
    
    for bin_id in bins:
        try:
            if sleep_bin(bin_id):
                success_count += 1
            else:
                failed_bins.append(bin_id)
        except Exception as e:
            logger.error(f"Failed to sleep {bin_id}: {e}")
            failed_bins.append(bin_id)
    
    # Zone broadcast
    zone_topic = f"cleanroute/zones/{zone_id}/command"
    payload = {
        "command": "sleep",
        "zone_id": zone_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        if command_client is None:
            init_command_client()
        command_client.publish(zone_topic, json.dumps(payload), qos=1)
        logger.info(f"Broadcast sleep to zone {zone_id}")
    except Exception as e:
        logger.error(f"Zone broadcast failed: {e}")
    
    return {
        "success": success_count > 0,
        "zone_id": zone_id,
        "zone_name": zone_name,
        "bins_asleep": success_count,
        "bins_failed": failed_bins,
        "total_bins": len(bins),
        "ended_at": datetime.utcnow().isoformat()
    }


def request_zone_status(zone_id: str, zone_name: str = None) -> Dict[str, Any]:
    """
    Request immediate status update from all bins in a zone.
    Used to check if bins have reported after wake-up or before finishing.
    
    Returns:
        Status of the request operation
    """
    bins = get_bins_in_zone(zone_id)
    
    if not bins:
        return {
            "success": False,
            "zone_id": zone_id,
            "zone_name": zone_name,
            "message": "No bins found in this zone",
            "bins_count": 0
        }
    
    # Request status from each bin
    success_count = 0
    for bin_id in bins:
        try:
            if request_status(bin_id):
                success_count += 1
        except Exception as e:
            logger.error(f"Failed to request status from {bin_id}: {e}")
    
    # Zone broadcast
    zone_topic = f"cleanroute/zones/{zone_id}/command"
    payload = {
        "command": "get_status",
        "zone_id": zone_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        if command_client is None:
            init_command_client()
        command_client.publish(zone_topic, json.dumps(payload), qos=1)
    except Exception as e:
        logger.error(f"Zone broadcast failed: {e}")
    
    return {
        "success": success_count > 0,
        "zone_id": zone_id,
        "zone_name": zone_name,
        "bins_requested": success_count,
        "total_bins": len(bins),
        "requested_at": datetime.utcnow().isoformat()
    }


# ─────────────────────────────────────────────────────────────────────────────
# IoT Enhanced Commands
# ─────────────────────────────────────────────────────────────────────────────

def send_command_with_ack(
    bin_id: str,
    command_type: str,
    payload: Optional[Dict[str, Any]] = None,
    qos: int = 1
) -> Dict[str, Any]:
    """
    Send a command that expects acknowledgment from the device.
    Creates a pending command record for tracking.
    """
    import uuid
    
    command_id = str(uuid.uuid4())[:8]
    
    # Create pending command record
    db.create_pending_command(command_id, bin_id, command_type, payload)
    
    # Include command_id in payload for device to echo back
    command_payload = payload or {}
    command_payload["command_id"] = command_id
    
    success = send_command(bin_id, command_type, command_payload, qos)
    
    return {
        "command_id": command_id,
        "bin_id": bin_id,
        "command_type": command_type,
        "sent": success,
        "awaiting_ack": success,
        "timestamp": datetime.utcnow().isoformat()
    }


def request_heartbeat(bin_id: str) -> bool:
    """Request a heartbeat from a device."""
    return send_command(bin_id, "heartbeat", qos=1)


def request_diagnostic(bin_id: str, diagnostic_type: str = "full") -> Dict[str, Any]:
    """
    Request diagnostic information from a device.
    
    Args:
        bin_id: Target device
        diagnostic_type: Type of diagnostic (full, sensors, network, memory)
    
    Returns:
        Diagnostic request info
    """
    # Create diagnostic record
    diag_id = db.request_diagnostic(bin_id, diagnostic_type)
    
    payload = {
        "diagnostic_id": diag_id,
        "diagnostic_type": diagnostic_type,
        "include": {
            "sensors": True,
            "network": True,
            "memory": True,
            "battery": True,
            "firmware": True
        } if diagnostic_type == "full" else {diagnostic_type: True}
    }
    
    success = send_command(bin_id, "diagnostic", payload, qos=1)
    
    return {
        "diagnostic_id": diag_id,
        "bin_id": bin_id,
        "diagnostic_type": diagnostic_type,
        "requested": success,
        "timestamp": datetime.utcnow().isoformat()
    }


def send_firmware_update(
    bin_id: str,
    version: str,
    file_url: str,
    checksum: str,
    file_size_kb: int
) -> Dict[str, Any]:
    """
    Send firmware update command to a device.
    
    Args:
        bin_id: Target device
        version: Target firmware version
        file_url: URL to download firmware
        checksum: SHA256 checksum of firmware file
        file_size_kb: File size in KB
    """
    # Get current firmware version from shadow
    shadow = db.get_device_shadow(bin_id)
    current_version = None
    if shadow and shadow.get('reported_state'):
        current_version = shadow['reported_state'].get('firmware_version')
    
    # Create update record
    update_id = db.create_firmware_update(bin_id, version, current_version)
    
    payload = {
        "update_id": update_id,
        "version": version,
        "url": file_url,
        "checksum": checksum,
        "size_kb": file_size_kb,
        "action": "download_and_install"
    }
    
    success = send_command(bin_id, "firmware_update", payload, qos=1)
    
    return {
        "update_id": update_id,
        "bin_id": bin_id,
        "target_version": version,
        "current_version": current_version,
        "initiated": success,
        "timestamp": datetime.utcnow().isoformat()
    }


def send_bulk_firmware_update(
    zone_id: str,
    version: str,
    file_url: str,
    checksum: str,
    file_size_kb: int
) -> Dict[str, Any]:
    """
    Send firmware update to all devices in a zone.
    """
    bins = get_bins_in_zone(zone_id)
    
    if not bins:
        return {
            "success": False,
            "message": "No bins found in zone",
            "zone_id": zone_id
        }
    
    results = []
    for bin_id in bins:
        result = send_firmware_update(bin_id, version, file_url, checksum, file_size_kb)
        results.append(result)
    
    successful = sum(1 for r in results if r.get('initiated'))
    
    return {
        "success": successful > 0,
        "zone_id": zone_id,
        "target_version": version,
        "devices_total": len(bins),
        "devices_initiated": successful,
        "devices_failed": len(bins) - successful,
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }


def update_device_shadow_desired(bin_id: str, desired_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the desired state of a device shadow and notify device.
    """
    db.update_device_shadow_desired(bin_id, desired_state)
    
    # Notify device of desired state change
    payload = {
        "action": "shadow_update",
        "desired": desired_state
    }
    
    success = send_command(bin_id, "shadow_delta", payload, qos=1)
    
    return {
        "bin_id": bin_id,
        "desired_state": desired_state,
        "notified": success,
        "timestamp": datetime.utcnow().isoformat()
    }


def retry_pending_commands(max_age_seconds: int = 60) -> Dict[str, Any]:
    """
    Retry commands that haven't been acknowledged.
    Should be called periodically (e.g., every 30 seconds).
    """
    pending = db.get_pending_commands(older_than_seconds=max_age_seconds)
    
    retried = 0
    failed = 0
    
    for cmd in pending:
        if cmd['retry_count'] >= cmd['max_retries']:
            db.mark_command_failed(cmd['command_id'], "Max retries exceeded")
            failed += 1
            logger.warning(f"Command {cmd['command_id']} to {cmd['bin_id']} failed after {cmd['retry_count']} retries")
        else:
            # Retry the command
            payload = cmd.get('payload', {})
            if isinstance(payload, str):
                import json
                payload = json.loads(payload)
            
            success = send_command(cmd['bin_id'], cmd['command_type'], payload, qos=1)
            if success:
                db.increment_command_retry(cmd['command_id'])
                retried += 1
                logger.info(f"Retried command {cmd['command_id']} to {cmd['bin_id']} (attempt {cmd['retry_count'] + 1})")
    
    return {
        "pending_checked": len(pending),
        "retried": retried,
        "failed": failed,
        "timestamp": datetime.utcnow().isoformat()
    }


def check_device_heartbeats(timeout_minutes: int = 5) -> Dict[str, Any]:
    """
    Check for devices that haven't sent heartbeats and mark them offline.
    Should be called periodically.
    """
    from . import db
    
    stale_devices = db.get_devices_needing_heartbeat(timeout_minutes)
    
    marked_offline = 0
    for device in stale_devices:
        # Mark as offline
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE bins SET device_status = 'offline' WHERE bin_id = %s",
                (device['bin_id'],)
            )
        marked_offline += 1
        logger.warning(f"Device {device['bin_id']} marked offline (no heartbeat for {timeout_minutes} min)")
    
    return {
        "devices_checked": len(stale_devices),
        "marked_offline": marked_offline,
        "timeout_minutes": timeout_minutes,
        "timestamp": datetime.utcnow().isoformat()
    }
