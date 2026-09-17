/**
 * TRUST GATE - ESP32 Physical Verification Gateway Firmware
 * Target: ESP32 DevKit v1 / ESP-WROOM-32
 * 
 * Hardware:
 * - 2.4" SPI TFT LCD (ILI9341 on dedicated VSPI bus)
 * - MAX30102 Pulse Oximeter (I2C0 on GPIO 21/22)
 * - Capacitive Touch Button (GPIO 32)
 * - IR Presence Sensor (GPIO 34 - input only)
 * - Gate Servo Motor (PWM on GPIO 25)
 */

#include <Arduino.h>
#include <ArduinoJson.h>
#include "config.h"
#include "display_driver.h"
#include "sensor_manager.h"
#include "servo_controller.h"
#include "protocol.h"

// Peripherals
ILI9341DisplayDriver display;
SensorManager sensors;
GateServoController gate;

unsigned long last_heartbeat_time = 0;
String serial_rx_buffer = "";

// Callback when gate auto-closes after timeout
void onGateClosed() {
    SerialProtocol::sendEvent("GATE_CLOSED");
    display.showWaiting();
}

void setup() {
    Serial.begin(SERIAL_BAUD_RATE);
    delay(200);

    Serial.println("\n[TRUST GATE] Initializing ESP32 Physical Access Gateway...");

    // 1. Startup Hardware Pin Conflict Validation
    if (!validateHardwareConfiguration()) {
        Serial.println("[FATAL] Hardware pin conflict detected! Execution halted for safety.");
        while (1) {
            delay(1000);
        }
    }

    // 2. Initialize Display
    display.begin();
    display.showWaiting();

    // 3. Initialize Sensors
    sensors.begin();

    // 4. Initialize Gate Servo
    gate.begin();

    // 5. Send DEVICE_READY handshake
    SerialProtocol::sendDeviceReady(sensors.isMax30102Available(), true);
    Serial.println("[TRUST GATE] Initialization complete. System ready.");
}

void processIncomingCommand(const String& json_str) {
    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, json_str);
    if (err) {
        Serial.printf("{\"event\":\"ERROR\",\"reason\":\"JSON_PARSE_ERROR\",\"msg\":\"%s\"}\n", err.c_str());
        return;
    }

    const char* command = doc["command"];
    if (!command) return;

    if (strcmp(command, "OPEN_GATE") == 0) {
        const char* cmd_id = doc["command_id"] | "";
        unsigned long duration = doc["duration_ms"] | GATE_OPEN_DURATION_MS;

        bool opened = gate.openGate(String(cmd_id), duration);
        if (opened) {
            SerialProtocol::sendEvent("GATE_OPENED");
            display.showAccessGranted();
        }
    }
    else if (strcmp(command, "LOCK_GATE") == 0) {
        gate.lockImmediate();
        SerialProtocol::sendEvent("GATE_CLOSED");
        display.showWaiting();
    }
    else if (strcmp(command, "SET_LCD") == 0) {
        const char* screen = doc["screen"] | "WAITING";
        const char* msg = doc["message"] | "";

        if (strcmp(screen, "WAITING") == 0) {
            display.showWaiting();
        } else if (strcmp(screen, "TOUCH_TO_START") == 0) {
            display.showTouchToStart();
        } else if (strcmp(screen, "SCANNING") == 0) {
            display.showStep(1, 5, "Document & Selfie Scan");
        } else if (strcmp(screen, "LIVENESS") == 0) {
            display.showLivenessPrompt(0, 0);
        } else if (strcmp(screen, "ACCESS_GRANTED") == 0) {
            display.showAccessGranted();
        } else if (strcmp(screen, "REVIEW_REQUIRED") == 0) {
            display.showReviewRequired(msg);
        } else if (strcmp(screen, "VERIFICATION_FAILED") == 0) {
            display.showVerificationFailed(msg);
        }
    }
    else if (strcmp(command, "START_LIVENESS") == 0) {
        unsigned long timeout = doc["timeout_ms"] | LIVENESS_SAMPLE_WINDOW_MS;
        sensors.startLivenessMeasurement(timeout);
        display.showLivenessPrompt(0, 0);
    }
    else if (strcmp(command, "RESET") == 0) {
        gate.lockImmediate();
        display.showWaiting();
        SerialProtocol::sendEvent("RESET_COMPLETE");
    }
}

void loop() {
    // 1. Update non-blocking servo timer
    gate.update(onGateClosed);

    // 2. Read incoming serial commands
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            if (serial_rx_buffer.length() > 0) {
                processIncomingCommand(serial_rx_buffer);
                serial_rx_buffer = "";
            }
        } else {
            serial_rx_buffer += c;
        }
    }

    // 3. Monitor Liveness state if currently sampling
    if (sensors.isLivenessActive()) {
        LivenessResult result;
        int progress_pct = 0;
        int display_bpm = 0;
        bool finished = sensors.updateLiveness(result, progress_pct, display_bpm);

        // Update LCD progress every 200ms
        static unsigned long last_live_update = 0;
        if (millis() - last_live_update > 200) {
            last_live_update = millis();
            display.showLivenessPrompt(progress_pct, display_bpm);
        }

        if (finished) {
            SerialProtocol::sendLivenessResult(
                result.pulse_detected,
                result.signal_quality,
                result.bpm,
                result.duration_ms
            );
        }
    }

    // 4. Check Presence and Touch triggers only when gate is locked & idle
    if (gate.isLocked() && !sensors.isLivenessActive()) {
        // IR Presence check
        if (sensors.checkPresenceDetected()) {
            SerialProtocol::sendEvent("PERSON_DETECTED");
            display.showTouchToStart();
        }

        // Capacitive Touch check
        if (sensors.checkTouchTriggered()) {
            SerialProtocol::sendEvent("VERIFICATION_STARTED");
            display.showStep(1, 5, "Starting Capture");
        }
    }

    // 5. Periodic Heartbeat (Every 5 seconds)
    if (millis() - last_heartbeat_time >= 5000) {
        last_heartbeat_time = millis();
        SerialProtocol::sendHeartbeat(
            digitalRead(PIN_IR_SENSOR) == LOW,
            digitalRead(PIN_TOUCH_BUTTON) == HIGH,
            sensors.isMax30102Available(),
            gate.isLocked() ? "LOCKED" : "OPEN"
        );
    }

    delay(10); // Yield for background Wi-Fi / FreeRTOS tasks
}
