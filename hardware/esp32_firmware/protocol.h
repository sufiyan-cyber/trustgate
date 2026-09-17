#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include "config.h"

class SerialProtocol {
public:
    static void sendEvent(const char* event_name) {
        StaticJsonDocument<128> doc;
        doc["device_id"] = DEVICE_ID;
        doc["event"] = event_name;
        serializeJson(doc, Serial);
        Serial.println();
    }

    static void sendDeviceReady(bool max30102_ok, bool servo_ok) {
        StaticJsonDocument<256> doc;
        doc["device_id"] = DEVICE_ID;
        doc["event"] = "DEVICE_READY";
        doc["firmware"] = "1.0.0";
        JsonObject sensors = doc.createNestedObject("sensors");
        sensors["ir"] = true;
        sensors["touch"] = true;
        sensors["max30102"] = max30102_ok;
        sensors["servo"] = servo_ok;
        serializeJson(doc, Serial);
        Serial.println();
    }

    static void sendLivenessResult(bool detected, float quality, float bpm, unsigned long duration_ms) {
        StaticJsonDocument<256> doc;
        doc["device_id"] = DEVICE_ID;
        doc["event"] = "LIVENESS_RESULT";
        doc["pulse_detected"] = detected;
        doc["signal_quality"] = quality;
        doc["bpm"] = bpm;
        doc["duration_ms"] = duration_ms;
        serializeJson(doc, Serial);
        Serial.println();
    }

    static void sendHeartbeat(bool ir, bool touch, bool max30102, const char* gate_state) {
        StaticJsonDocument<256> doc;
        doc["device_id"] = DEVICE_ID;
        doc["event"] = "HEARTBEAT";
        JsonObject sensors = doc.createNestedObject("sensors");
        sensors["ir"] = ir;
        sensors["touch"] = touch;
        sensors["max30102"] = max30102;
        sensors["gate"] = gate_state;
        serializeJson(doc, Serial);
        Serial.println();
    }
};

#endif // PROTOCOL_H
