# ESP32 Hardware Developer Guide - CleanRoute Smart Bin

## Device Configuration: COL404

This document provides all the information needed to program an ESP32 microcontroller for the CleanRoute smart waste bin monitoring system.

---

## 1. MQTT Broker Connection Details

### Connection Parameters
```
Host:        localhost (replace with your server IP/domain in production)
Port:        8883 (TLS) or 1883 (non-TLS for testing only)
Protocol:    MQTT 3.1.1
Client ID:   COL404
Keep Alive:  60 seconds
Clean Session: true
```

### Device Authentication
```
Username: COL404
Password: col_zone4_404
```

### TLS/SSL Configuration (Required for Production)
- **TLS Version:** TLS 1.2 or higher
- **Verify Server Certificate:** Yes
- **CA Certificate:** See Section 10 below

---

## 2. MQTT Topics

### Topics Device PUBLISHES TO (Uplink - Device to Server):

| Topic | QoS | Purpose | Frequency |
|-------|-----|---------|-----------|
| `bins/COL404/telemetry` | 1 | Fill level, battery, temp | Every 5-15 min |
| `bins/COL404/heartbeat` | 1 | Connectivity check | Every 1-2 min |
| `bins/COL404/ack` | 1 | Command acknowledgment | On command received |
| `bins/COL404/power` | 1 | Power/battery profile | Every 30 min |
| `bins/COL404/diagnostics` | 1 | System health | Every 1 hour |

### Topics Device SUBSCRIBES TO (Downlink - Server to Device):

| Topic | QoS | Purpose |
|-------|-----|---------|
| `bins/COL404/commands` | 1 | Receive commands from server |

---

## 3. Message Payloads (JSON Format)

### A. Telemetry Message
**Topic:** `bins/COL404/telemetry`  
**Frequency:** Every 5-15 minutes (configurable)  
**QoS:** 1

```json
{
    "bin_id": "COL404",
    "fill_level": 45.5,
    "temperature": 28.3,
    "battery_level": 85,
    "timestamp": "2025-12-14T10:30:00Z"
}
```

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `bin_id` | string | - | Device identifier (always "COL404") |
| `fill_level` | float | % | 0-100, ultrasonic sensor reading |
| `temperature` | float | Celsius | Ambient temperature |
| `battery_level` | int | % | 0-100, battery percentage |
| `timestamp` | string | ISO 8601 UTC | Current time |

### B. Heartbeat Message
**Topic:** `bins/COL404/heartbeat`  
**Frequency:** Every 1-2 minutes  
**QoS:** 1

```json
{
    "bin_id": "COL404",
    "timestamp": "2025-12-14T10:30:00Z",
    "rssi_dbm": -65,
    "uptime_seconds": 3600
}
```

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `bin_id` | string | - | Device identifier |
| `timestamp` | string | ISO 8601 UTC | Current time |
| `rssi_dbm` | int | dBm | WiFi signal strength (negative value) |
| `uptime_seconds` | int | seconds | Time since last boot |

### C. Power Profile Message
**Topic:** `bins/COL404/power`  
**Frequency:** Every 30 minutes  
**QoS:** 1

```json
{
    "bin_id": "COL404",
    "battery_voltage": 3.7,
    "solar_voltage": 4.2,
    "current_draw_ma": 15,
    "power_mode": "normal",
    "sleep_interval_s": 300,
    "timestamp": "2025-12-14T10:30:00Z"
}
```

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `battery_voltage` | float | Volts | Battery voltage (3.0-4.2V typical) |
| `solar_voltage` | float | Volts | Solar panel voltage (0 if no panel) |
| `current_draw_ma` | int | mA | Current power consumption |
| `power_mode` | string | - | `"normal"`, `"low_power"`, or `"solar_charging"` |
| `sleep_interval_s` | int | seconds | Time between wake cycles |

### D. Diagnostics Message
**Topic:** `bins/COL404/diagnostics`  
**Frequency:** Every 1 hour  
**QoS:** 1

```json
{
    "bin_id": "COL404",
    "uptime_seconds": 86400,
    "free_memory_bytes": 32768,
    "cpu_temp_c": 45.2,
    "error_count": 0,
    "restart_count": 2,
    "last_error": null,
    "firmware_version": "1.0.0",
    "timestamp": "2025-12-14T10:30:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `uptime_seconds` | int | Total uptime since last restart |
| `free_memory_bytes` | int | Available heap memory |
| `cpu_temp_c` | float | ESP32 internal temperature |
| `error_count` | int | Number of errors since boot |
| `restart_count` | int | Number of restarts (store in RTC memory) |
| `last_error` | string/null | Last error message or null |
| `firmware_version` | string | Current firmware version |

### E. Command Acknowledgment Message
**Topic:** `bins/COL404/ack`  
**Frequency:** Immediately after receiving any command  
**QoS:** 1

```json
{
    "command_id": "abc-123-def-456",
    "bin_id": "COL404",
    "status": "success",
    "error": null,
    "timestamp": "2025-12-14T10:30:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `command_id` | string | UUID from the received command (echo back) |
| `status` | string | `"success"` or `"failed"` |
| `error` | string/null | Error message if failed, null if success |

---

## 4. Handling Incoming Commands

**Subscribe to:** `bins/COL404/commands`

### Incoming Command Format:
```json
{
    "command": "wake",
    "command_id": "abc-123-def-456",
    "params": {},
    "timestamp": "2025-12-14T10:30:00Z"
}
```

### Command Types to Handle:

| Command | Params | Action Required |
|---------|--------|-----------------|
| `wake` | `{}` | Exit sleep mode, resume normal telemetry |
| `sleep` | `{"duration_minutes": 30}` | Enter deep sleep for specified duration |
| `configure` | `{"report_interval_s": 600, "fill_threshold": 80}` | Update device settings |
| `ota_update` | `{"version": "1.1.0", "url": "...", "checksum": "sha256:..."}` | Download and install firmware |
| `reboot` | `{}` | Restart the device |
| `request_diagnostics` | `{}` | Immediately publish diagnostics message |

### Command Handling Flow:
```
1. Receive message on bins/COL404/commands
2. Parse JSON, extract "command" and "command_id"
3. Execute the command
4. Publish ACK to bins/COL404/ack with same command_id
5. If command is "reboot", send ACK first, then restart
```

**IMPORTANT:** The server will retry commands up to 3 times if no ACK is received within 30 seconds.

---

## 5. Hardware Requirements

### Recommended Components

| Component | Model | Purpose | GPIO |
|-----------|-------|---------|------|
| Microcontroller | ESP32-WROOM-32 | Main processor | - |
| Ultrasonic Sensor | HC-SR04 or JSN-SR04T | Fill level measurement | Trig: GPIO5, Echo: GPIO18 |
| Temperature Sensor | DS18B20 or DHT22 | Ambient temperature | GPIO4 |
| Battery | 18650 Li-Ion (3.7V) | Power source | - |
| Voltage Divider | 100K/100K resistors | Battery monitoring | GPIO34 (ADC1_CH6) |
| Solar Panel (optional) | 5V/1W | Solar charging | GPIO35 (ADC1_CH7) |
| Charge Controller | TP4056 | Battery charging | - |

### Wiring Diagram
```
ESP32 GPIO Assignments:
------------------------
GPIO5  -> Ultrasonic Trig
GPIO18 -> Ultrasonic Echo
GPIO4  -> Temperature Sensor (OneWire)
GPIO34 -> Battery Voltage (via voltage divider)
GPIO35 -> Solar Voltage (via voltage divider)
GPIO2  -> Status LED (onboard)
```

---

## 6. Fill Level Calculation

Using ultrasonic sensor to measure distance to trash:

```cpp
// Bin dimensions
const float BIN_HEIGHT_CM = 100.0;  // Total height of bin
const float SENSOR_OFFSET_CM = 5.0;  // Sensor mounted 5cm from top

float calculateFillLevel() {
    // Measure distance to trash surface
    float distance_cm = measureUltrasonic();
    
    // Calculate fill level
    float empty_distance = BIN_HEIGHT_CM - SENSOR_OFFSET_CM;
    float fill_level = ((empty_distance - distance_cm) / empty_distance) * 100.0;
    
    // Clamp to valid range
    if (fill_level < 0) fill_level = 0;
    if (fill_level > 100) fill_level = 100;
    
    return fill_level;
}
```

---

## 7. Power Management

### Deep Sleep Implementation
```cpp
#include "esp_sleep.h"

void enterDeepSleep(int duration_minutes) {
    // Convert to microseconds
    uint64_t sleep_time_us = duration_minutes * 60 * 1000000ULL;
    
    // Configure wake up
    esp_sleep_enable_timer_wakeup(sleep_time_us);
    
    // Enter deep sleep
    esp_deep_sleep_start();
}
```

### Power Modes
| Mode | Current Draw | Description |
|------|--------------|-------------|
| Active | ~80-150mA | Normal operation, WiFi connected |
| Light Sleep | ~0.8mA | CPU paused, WiFi maintained |
| Deep Sleep | ~10uA | Everything off, wake on timer |

---

## 8. Complete ESP32 Arduino Code

```cpp
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "esp_sleep.h"
#include "time.h"

// ============== CONFIGURATION ==============

// WiFi Credentials
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// MQTT Configuration
const char* MQTT_SERVER = "YOUR_SERVER_IP";  // Replace with server IP
const int MQTT_PORT = 8883;                   // TLS port
const char* MQTT_USER = "COL404";
const char* MQTT_PASS = "col_zone4_404";
const char* CLIENT_ID = "COL404";
const char* BIN_ID = "COL404";

// MQTT Topics
const char* TOPIC_TELEMETRY = "bins/COL404/telemetry";
const char* TOPIC_HEARTBEAT = "bins/COL404/heartbeat";
const char* TOPIC_ACK = "bins/COL404/ack";
const char* TOPIC_POWER = "bins/COL404/power";
const char* TOPIC_DIAGNOSTICS = "bins/COL404/diagnostics";
const char* TOPIC_COMMANDS = "bins/COL404/commands";

// Timing Configuration (milliseconds)
const unsigned long HEARTBEAT_INTERVAL = 60000;    // 1 minute
const unsigned long TELEMETRY_INTERVAL = 300000;   // 5 minutes
const unsigned long POWER_INTERVAL = 1800000;      // 30 minutes
const unsigned long DIAGNOSTICS_INTERVAL = 3600000; // 1 hour

// GPIO Pins
const int PIN_ULTRASONIC_TRIG = 5;
const int PIN_ULTRASONIC_ECHO = 18;
const int PIN_TEMPERATURE = 4;
const int PIN_BATTERY_ADC = 34;
const int PIN_SOLAR_ADC = 35;
const int PIN_LED = 2;

// Bin Configuration
const float BIN_HEIGHT_CM = 100.0;
const float SENSOR_OFFSET_CM = 5.0;

// Firmware Version
const char* FIRMWARE_VERSION = "1.0.0";

// CA Certificate (from mqtt/certs/ca.crt)
const char* CA_CERT = R"EOF(
-----BEGIN CERTIFICATE-----
MIIDVTCCAj2gAwIBAgIUE3k8KC8x5p5oOqqsQWecNGuNJiQwDQYJKoZIhvcNAQEL
BQAwOjEWMBQGA1UEAwwNQ2xlYW5Sb3V0ZS1DQTETMBEGA1UECgwKQ2xlYW5Sb3V0
ZTELMAkGA1UEBhMCTEswHhcNMjUxMjEzMTAwNDEyWhcNMjYxMjEzMTAwNDEyWjA6
MRYwFAYDVQQDDA1DbGVhblJvdXRlLUNBMRMwEQYDVQQKDApDbGVhblJvdXRlMQsw
CQYDVQQGEwJMSzCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKfpeh2s
loXRg5Vgy6qf+uwVfYikl3XGwNFFyTdPbBRhximLnKnjhTtrjwCjPVwvBVMJiSzu
Mr9sb1Ok1iG3HKNkaSQJQDZ0FWpxSs6E3B5IH/pgWsM91dbNTKcO5PAs/HxPayjP
a44OHsCvv2ALWWYS4jvtTF4rAauhpS3bgrZA8KzgK9E5NI6x4dDeQzThpfNgWanp
uH/38nOOjQp0LjCf6ZarwvlxE5h3LpTw+Oiab/JQr4KEzM6nlD8YNLeC870XcKnL
Si0k/Yut3DdBUSt62/XhZ1thOtpOqaMqysGqrmxwJdyWQIJLbzDHP7riU+Gkhgr0
2iIVbNzvYqLq89cCAwEAAaNTMFEwHQYDVR0OBBYEFFMvsN/BZMfGOlIQxs6sEy+1
VJVfMB8GA1UdIwQYMBaAFFMvsN/BZMfGOlIQxs6sEy+1VJVfMA8GA1UdEwEB/wQF
MAMBAf8wDQYJKoZIhvcNAQELBQADggEBACGS0WxUV3i7jf93YMXeCiUikR9NfMbi
DQrqmrJoLiFODXRT6vFxNAOTVMdGBVcRola4sWhgm2I4CgmEZptpKXI33oyAEsVD
kFXDMjC6Kc8/C5ZNmFFzbTzWQu9OFPfof2f7b4gUg8vtMngIm6hMjPq3GDq7jYlw
swH2d5nwAcCw/9Vlte6f62lmUvm9gVFs5hpYFuFUCOUnCRTJdYjH4h9gyatR8LP/
sMHJnxhKdEiVcruCklDu3fbvl6lOx+9kza1pClx0a1U4bDKFAfYIeG5g8qFzRs4K
aielg1+nHqcg5IDtMcfieC89IB7YqPBnW0p5z4XgRK8+E2sGZL6yvrg=
-----END CERTIFICATE-----
)EOF";

// ============== GLOBAL VARIABLES ==============

WiFiClientSecure espClient;
PubSubClient mqtt(espClient);

unsigned long lastHeartbeat = 0;
unsigned long lastTelemetry = 0;
unsigned long lastPower = 0;
unsigned long lastDiagnostics = 0;
unsigned long bootTime = 0;
int errorCount = 0;
RTC_DATA_ATTR int restartCount = 0;  // Persists through deep sleep
String lastError = "";
bool sleepMode = false;

// ============== SETUP ==============

void setup() {
    Serial.begin(115200);
    Serial.println("\n=== CleanRoute Smart Bin - COL404 ===");
    
    restartCount++;
    bootTime = millis();
    
    // Initialize GPIO
    pinMode(PIN_ULTRASONIC_TRIG, OUTPUT);
    pinMode(PIN_ULTRASONIC_ECHO, INPUT);
    pinMode(PIN_LED, OUTPUT);
    
    // Connect to WiFi
    connectWiFi();
    
    // Configure time (for timestamps)
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    
    // Setup TLS
    espClient.setCACert(CA_CERT);
    
    // Setup MQTT
    mqtt.setServer(MQTT_SERVER, MQTT_PORT);
    mqtt.setCallback(onCommandReceived);
    mqtt.setBufferSize(512);
    
    // Connect to MQTT
    connectMQTT();
    
    // Send initial diagnostics
    sendDiagnostics();
    
    Serial.println("Setup complete!");
}

// ============== MAIN LOOP ==============

void loop() {
    // Maintain connections
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }
    if (!mqtt.connected()) {
        connectMQTT();
    }
    mqtt.loop();
    
    unsigned long now = millis();
    
    // Heartbeat - every 1 minute
    if (now - lastHeartbeat >= HEARTBEAT_INTERVAL) {
        sendHeartbeat();
        lastHeartbeat = now;
    }
    
    // Telemetry - every 5 minutes
    if (now - lastTelemetry >= TELEMETRY_INTERVAL) {
        sendTelemetry();
        lastTelemetry = now;
    }
    
    // Power profile - every 30 minutes
    if (now - lastPower >= POWER_INTERVAL) {
        sendPowerProfile();
        lastPower = now;
    }
    
    // Diagnostics - every 1 hour
    if (now - lastDiagnostics >= DIAGNOSTICS_INTERVAL) {
        sendDiagnostics();
        lastDiagnostics = now;
    }
    
    // Blink LED to show activity
    digitalWrite(PIN_LED, (millis() / 1000) % 2);
}

// ============== WIFI CONNECTION ==============

void connectWiFi() {
    Serial.print("Connecting to WiFi");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println(" Connected!");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println(" Failed!");
        lastError = "WiFi connection failed";
        errorCount++;
    }
}

// ============== MQTT CONNECTION ==============

void connectMQTT() {
    Serial.print("Connecting to MQTT");
    
    int attempts = 0;
    while (!mqtt.connected() && attempts < 5) {
        if (mqtt.connect(CLIENT_ID, MQTT_USER, MQTT_PASS)) {
            Serial.println(" Connected!");
            // Subscribe to commands
            mqtt.subscribe(TOPIC_COMMANDS, 1);
            Serial.println("Subscribed to commands topic");
        } else {
            Serial.print(".");
            Serial.print(" Error: ");
            Serial.println(mqtt.state());
            delay(2000);
            attempts++;
        }
    }
    
    if (!mqtt.connected()) {
        lastError = "MQTT connection failed";
        errorCount++;
    }
}

// ============== COMMAND HANDLER ==============

void onCommandReceived(char* topic, byte* payload, unsigned int length) {
    Serial.println("\n>>> Command received!");
    
    // Parse JSON
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, payload, length);
    
    if (error) {
        Serial.print("JSON parse error: ");
        Serial.println(error.c_str());
        return;
    }
    
    const char* command = doc["command"];
    const char* commandId = doc["command_id"];
    
    Serial.print("Command: ");
    Serial.println(command);
    Serial.print("Command ID: ");
    Serial.println(commandId);
    
    bool success = true;
    String errorMsg = "";
    
    // Handle commands
    if (strcmp(command, "wake") == 0) {
        sleepMode = false;
        Serial.println("Exiting sleep mode");
        
    } else if (strcmp(command, "sleep") == 0) {
        int duration = doc["params"]["duration_minutes"] | 30;
        Serial.printf("Entering sleep for %d minutes\n", duration);
        sendAck(commandId, true, NULL);
        delay(100);
        enterDeepSleep(duration);
        
    } else if (strcmp(command, "configure") == 0) {
        // Update configuration
        Serial.println("Configuration updated");
        
    } else if (strcmp(command, "reboot") == 0) {
        Serial.println("Rebooting...");
        sendAck(commandId, true, NULL);
        delay(100);
        ESP.restart();
        
    } else if (strcmp(command, "request_diagnostics") == 0) {
        sendDiagnostics();
        
    } else if (strcmp(command, "ota_update") == 0) {
        // OTA update handling
        const char* version = doc["params"]["version"];
        Serial.printf("OTA update to version %s requested\n", version);
        // Implement OTA logic here
        
    } else {
        success = false;
        errorMsg = "Unknown command";
    }
    
    // Send acknowledgment
    sendAck(commandId, success, success ? NULL : errorMsg.c_str());
}

// ============== SEND FUNCTIONS ==============

void sendAck(const char* commandId, bool success, const char* error) {
    StaticJsonDocument<256> doc;
    doc["command_id"] = commandId;
    doc["bin_id"] = BIN_ID;
    doc["status"] = success ? "success" : "failed";
    doc["error"] = error;
    doc["timestamp"] = getTimestamp();
    
    char buffer[256];
    serializeJson(doc, buffer);
    mqtt.publish(TOPIC_ACK, buffer, false);
    Serial.println("ACK sent");
}

void sendHeartbeat() {
    StaticJsonDocument<256> doc;
    doc["bin_id"] = BIN_ID;
    doc["timestamp"] = getTimestamp();
    doc["rssi_dbm"] = WiFi.RSSI();
    doc["uptime_seconds"] = (millis() - bootTime) / 1000;
    
    char buffer[256];
    serializeJson(doc, buffer);
    
    if (mqtt.publish(TOPIC_HEARTBEAT, buffer, false)) {
        Serial.println("Heartbeat sent");
    }
}

void sendTelemetry() {
    StaticJsonDocument<256> doc;
    doc["bin_id"] = BIN_ID;
    doc["fill_level"] = measureFillLevel();
    doc["temperature"] = measureTemperature();
    doc["battery_level"] = measureBatteryPercent();
    doc["timestamp"] = getTimestamp();
    
    char buffer[256];
    serializeJson(doc, buffer);
    
    if (mqtt.publish(TOPIC_TELEMETRY, buffer, false)) {
        Serial.println("Telemetry sent");
        Serial.println(buffer);
    }
}

void sendPowerProfile() {
    StaticJsonDocument<256> doc;
    doc["bin_id"] = BIN_ID;
    doc["battery_voltage"] = measureBatteryVoltage();
    doc["solar_voltage"] = measureSolarVoltage();
    doc["current_draw_ma"] = 50;  // Estimate or measure
    doc["power_mode"] = sleepMode ? "low_power" : "normal";
    doc["sleep_interval_s"] = TELEMETRY_INTERVAL / 1000;
    doc["timestamp"] = getTimestamp();
    
    char buffer[256];
    serializeJson(doc, buffer);
    
    if (mqtt.publish(TOPIC_POWER, buffer, false)) {
        Serial.println("Power profile sent");
    }
}

void sendDiagnostics() {
    StaticJsonDocument<384> doc;
    doc["bin_id"] = BIN_ID;
    doc["uptime_seconds"] = (millis() - bootTime) / 1000;
    doc["free_memory_bytes"] = ESP.getFreeHeap();
    doc["cpu_temp_c"] = temperatureRead();  // Internal temp sensor
    doc["error_count"] = errorCount;
    doc["restart_count"] = restartCount;
    doc["last_error"] = lastError.length() > 0 ? lastError : nullptr;
    doc["firmware_version"] = FIRMWARE_VERSION;
    doc["timestamp"] = getTimestamp();
    
    char buffer[384];
    serializeJson(doc, buffer);
    
    if (mqtt.publish(TOPIC_DIAGNOSTICS, buffer, false)) {
        Serial.println("Diagnostics sent");
    }
}

// ============== SENSOR FUNCTIONS ==============

float measureFillLevel() {
    // Trigger ultrasonic pulse
    digitalWrite(PIN_ULTRASONIC_TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(PIN_ULTRASONIC_TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_ULTRASONIC_TRIG, LOW);
    
    // Measure echo time
    long duration = pulseIn(PIN_ULTRASONIC_ECHO, HIGH, 30000);
    
    // Calculate distance (speed of sound = 343 m/s)
    float distance_cm = duration * 0.0343 / 2;
    
    // Calculate fill level
    float empty_distance = BIN_HEIGHT_CM - SENSOR_OFFSET_CM;
    float fill_level = ((empty_distance - distance_cm) / empty_distance) * 100.0;
    
    // Clamp to valid range
    if (fill_level < 0) fill_level = 0;
    if (fill_level > 100) fill_level = 100;
    
    return fill_level;
}

float measureTemperature() {
    // Implement DS18B20 or DHT22 reading
    // For now, return a simulated value
    return 28.0 + (random(0, 100) / 50.0);
}

float measureBatteryVoltage() {
    int raw = analogRead(PIN_BATTERY_ADC);
    // Assuming 100K/100K voltage divider, 3.3V reference
    float voltage = (raw / 4095.0) * 3.3 * 2;
    return voltage;
}

int measureBatteryPercent() {
    float voltage = measureBatteryVoltage();
    // Li-Ion: 3.0V = 0%, 4.2V = 100%
    int percent = (int)((voltage - 3.0) / 1.2 * 100);
    if (percent < 0) percent = 0;
    if (percent > 100) percent = 100;
    return percent;
}

float measureSolarVoltage() {
    int raw = analogRead(PIN_SOLAR_ADC);
    float voltage = (raw / 4095.0) * 3.3 * 2;
    return voltage;
}

// ============== UTILITY FUNCTIONS ==============

String getTimestamp() {
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
        return "1970-01-01T00:00:00Z";
    }
    char buffer[25];
    strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    return String(buffer);
}

void enterDeepSleep(int duration_minutes) {
    Serial.printf("Entering deep sleep for %d minutes...\n", duration_minutes);
    
    // Disconnect cleanly
    mqtt.disconnect();
    WiFi.disconnect(true);
    
    // Configure wake up timer
    uint64_t sleep_time_us = duration_minutes * 60 * 1000000ULL;
    esp_sleep_enable_timer_wakeup(sleep_time_us);
    
    // Enter deep sleep
    esp_deep_sleep_start();
}
```

---

## 9. Testing Without TLS (Development Only)

For initial testing on local network:

```cpp
// Replace these lines:
WiFiClientSecure espClient;
const int MQTT_PORT = 8883;
espClient.setCACert(CA_CERT);

// With these:
WiFiClient espClient;  // Regular WiFiClient, not secure
const int MQTT_PORT = 1883;
// Remove setCACert line
```

**WARNING:** Always use TLS (port 8883) in production!

---

## 10. CA Certificate

Copy this entire certificate and paste into the `CA_CERT` variable:

```
-----BEGIN CERTIFICATE-----
MIIDVTCCAj2gAwIBAgIUE3k8KC8x5p5oOqqsQWecNGuNJiQwDQYJKoZIhvcNAQEL
BQAwOjEWMBQGA1UEAwwNQ2xlYW5Sb3V0ZS1DQTETMBEGA1UECgwKQ2xlYW5Sb3V0
ZTELMAkGA1UEBhMCTEswHhcNMjUxMjEzMTAwNDEyWhcNMjYxMjEzMTAwNDEyWjA6
MRYwFAYDVQQDDA1DbGVhblJvdXRlLUNBMRMwEQYDVQQKDApDbGVhblJvdXRlMQsw
CQYDVQQGEwJMSzCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKfpeh2s
loXRg5Vgy6qf+uwVfYikl3XGwNFFyTdPbBRhximLnKnjhTtrjwCjPVwvBVMJiSzu
Mr9sb1Ok1iG3HKNkaSQJQDZ0FWpxSs6E3B5IH/pgWsM91dbNTKcO5PAs/HxPayjP
a44OHsCvv2ALWWYS4jvtTF4rAauhpS3bgrZA8KzgK9E5NI6x4dDeQzThpfNgWanp
uH/38nOOjQp0LjCf6ZarwvlxE5h3LpTw+Oiab/JQr4KEzM6nlD8YNLeC870XcKnL
Si0k/Yut3DdBUSt62/XhZ1thOtpOqaMqysGqrmxwJdyWQIJLbzDHP7riU+Gkhgr0
2iIVbNzvYqLq89cCAwEAAaNTMFEwHQYDVR0OBBYEFFMvsN/BZMfGOlIQxs6sEy+1
VJVfMB8GA1UdIwQYMBaAFFMvsN/BZMfGOlIQxs6sEy+1VJVfMA8GA1UdEwEB/wQF
MAMBAf8wDQYJKoZIhvcNAQELBQADggEBACGS0WxUV3i7jf93YMXeCiUikR9NfMbi
DQrqmrJoLiFODXRT6vFxNAOTVMdGBVcRola4sWhgm2I4CgmEZptpKXI33oyAEsVD
kFXDMjC6Kc8/C5ZNmFFzbTzWQu9OFPfof2f7b4gUg8vtMngIm6hMjPq3GDq7jYlw
swH2d5nwAcCw/9Vlte6f62lmUvm9gVFs5hpYFuFUCOUnCRTJdYjH4h9gyatR8LP/
sMHJnxhKdEiVcruCklDu3fbvl6lOx+9kza1pClx0a1U4bDKFAfYIeG5g8qFzRs4K
aielg1+nHqcg5IDtMcfieC89IB7YqPBnW0p5z4XgRK8+E2sGZL6yvrg=
-----END CERTIFICATE-----
```

---

## 11. Arduino Libraries Required

Install these libraries via Arduino Library Manager:

| Library | Version | Purpose |
|---------|---------|---------|
| PubSubClient | 2.8+ | MQTT client |
| ArduinoJson | 6.x | JSON parsing |
| OneWire | 2.3+ | DS18B20 sensor (if using) |
| DallasTemperature | 3.9+ | DS18B20 sensor (if using) |

---

## 12. Quick Reference Card

```
Device: COL404
Password: col_zone4_404
MQTT Port: 8883 (TLS)

PUBLISH TOPICS:
  bins/COL404/telemetry    (every 5 min)
  bins/COL404/heartbeat    (every 1 min)
  bins/COL404/ack          (on command)
  bins/COL404/power        (every 30 min)
  bins/COL404/diagnostics  (every 1 hour)

SUBSCRIBE TOPIC:
  bins/COL404/commands

COMMANDS TO HANDLE:
  wake, sleep, configure, reboot, 
  request_diagnostics, ota_update

ALWAYS:
  - Use QoS 1 for all messages
  - Send ACK after every command
  - Use ISO 8601 UTC timestamps
  - Keep payloads under 200 bytes
```

---

## 13. Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't connect to WiFi | Check SSID/password, ensure 2.4GHz network |
| MQTT connection fails | Verify server IP, check TLS cert, verify credentials |
| No commands received | Ensure subscribed to commands topic after connect |
| Sensor reads 0 | Check wiring, verify GPIO pins |
| Battery voltage wrong | Verify voltage divider resistor values |

---

## Contact

For backend/server questions, contact the backend team.
Server repository: `github.com/ThevinduSK/cleanroute-backend`
