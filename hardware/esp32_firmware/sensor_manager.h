#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include <Arduino.h>
#include <Wire.h>
#include "config.h"

// SparkFun MAX3010x definitions
#define MAX30102_I2C_ADDR 0x57

struct LivenessResult {
    bool pulse_detected;
    float signal_quality;
    float bpm;
    unsigned long duration_ms;
    bool stable;
};

class SensorManager {
private:
    bool max30102_found;
    bool last_ir_state;
    unsigned long ir_detect_start;
    bool last_touch_state;
    unsigned long touch_debounce;

    // Liveness sampling
    bool liveness_active;
    unsigned long liveness_start_time;
    unsigned long liveness_target_ms;
    int sample_count;
    int beat_count;
    float running_bpm;

public:
    SensorManager() :
        max30102_found(false),
        last_ir_state(false),
        ir_detect_start(0),
        last_touch_state(false),
        touch_debounce(0),
        liveness_active(false),
        liveness_start_time(0),
        liveness_target_ms(LIVENESS_SAMPLE_WINDOW_MS),
        sample_count(0),
        beat_count(0),
        running_bpm(72.0) {}

    bool begin() {
        // Initialize IR pin as input
        pinMode(PIN_IR_SENSOR, INPUT);

        // Initialize Touch pin as input
        pinMode(PIN_TOUCH_BUTTON, INPUT_PULLDOWN);

        // Initialize I2C bus for MAX30102
        Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, I2C_CLOCK_SPEED);

        // Ping MAX30102 I2C address
        Wire.beginTransmission(MAX30102_I2C_ADDR);
        byte error = Wire.endTransmission();
        max30102_found = (error == 0);

        if (max30102_found) {
            // Configure basic MAX30102 registers (Mode Config, LED pulse amplitude)
            Wire.beginTransmission(MAX30102_I2C_ADDR);
            Wire.write(0x09); // Mode configuration
            Wire.write(0x03); // SpO2 mode (Red and IR LEDs active)
            Wire.endTransmission();
        }

        return true;
    }

    bool isMax30102Available() const {
        return max30102_found;
    }

    // Returns true on clean rising edge of presence detection
    bool checkPresenceDetected() {
        // IR obstacle sensors are typically active LOW (LOW when obstacle detected)
        int raw = digitalRead(PIN_IR_SENSOR);
        bool current_detected = (raw == LOW);

        if (current_detected && !last_ir_state) {
            if (ir_detect_start == 0) {
                ir_detect_start = millis();
            } else if (millis() - ir_detect_start >= 250) { // 250ms debounce
                last_ir_state = true;
                return true;
            }
        } else if (!current_detected) {
            last_ir_state = false;
            ir_detect_start = 0;
        }
        return false;
    }

    // Returns true on clean touch trigger
    bool checkTouchTriggered() {
        int raw = digitalRead(PIN_TOUCH_BUTTON);
        bool current_touch = (raw == HIGH);

        if (current_touch && !last_touch_state) {
            if (millis() - touch_debounce > 300) {
                last_touch_state = true;
                touch_debounce = millis();
                return true;
            }
        } else if (!current_touch) {
            last_touch_state = false;
        }
        return false;
    }

    void startLivenessMeasurement(unsigned long timeout_ms = LIVENESS_SAMPLE_WINDOW_MS) {
        liveness_active = true;
        liveness_start_time = millis();
        liveness_target_ms = timeout_ms;
        sample_count = 0;
        beat_count = 0;
        running_bpm = 72.0;
    }

    bool isLivenessActive() const {
        return liveness_active;
    }

    // Polls liveness sample; returns true when sampling duration completes
    bool updateLiveness(LivenessResult& result, int& progress_pct, int& display_bpm) {
        if (!liveness_active) return false;

        unsigned long elapsed = millis() - liveness_start_time;
        progress_pct = min(100, (int)((elapsed * 100) / liveness_target_ms));
        sample_count++;

        // Simulate systolic peak detection over window
        if (sample_count % 30 == 0) {
            beat_count++;
            running_bpm = 68.0 + (beat_count % 12);
        }
        display_bpm = (int)running_bpm;

        if (elapsed >= liveness_target_ms) {
            liveness_active = false;
            result.pulse_detected = true;
            result.signal_quality = 0.92f;
            result.bpm = running_bpm;
            result.duration_ms = elapsed;
            result.stable = true;
            return true;
        }
        return false;
    }
};

#endif // SENSOR_MANAGER_H
