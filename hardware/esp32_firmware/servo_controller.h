#ifndef SERVO_CONTROLLER_H
#define SERVO_CONTROLLER_H

#include <Arduino.h>
#include <ESP32Servo.h>
#include "config.h"

enum ServoState {
    GATE_LOCKED,
    GATE_OPENING,
    GATE_OPEN,
    GATE_CLOSING
};

class GateServoController {
private:
    Servo servo;
    ServoState state;
    unsigned long open_start_time;
    unsigned long open_duration_ms;
    String last_command_id;
    bool is_attached;

public:
    GateServoController() :
        state(GATE_LOCKED),
        open_start_time(0),
        open_duration_ms(GATE_OPEN_DURATION_MS),
        is_attached(false) {}

    bool begin() {
        // Allow allocation of all timers
        ESP32PWM::allocateTimer(0);
        ESP32PWM::allocateTimer(1);
        ESP32PWM::allocateTimer(2);
        ESP32PWM::allocateTimer(3);
        servo.setPeriodHertz(SERVO_LEDC_FREQ);
        
        // Attach to dedicated PIN_SERVO_GATE (GPIO 25)
        int res = servo.attach(PIN_SERVO_GATE, 500, 2400);
        is_attached = (res >= 0);
        lockImmediate();
        return is_attached;
    }

    void lockImmediate() {
        if (is_attached) {
            servo.write(SERVO_ANGLE_LOCKED);
        }
        state = GATE_LOCKED;
        open_start_time = 0;
    }

    bool openGate(const String& command_id, unsigned long duration_ms = GATE_OPEN_DURATION_MS) {
        // Replay rejection
        if (command_id.length() > 0 && command_id == last_command_id) {
            Serial.println("{\"event\":\"ERROR\",\"reason\":\"REPLAY_COMMAND_REJECTED\"}");
            return false;
        }

        last_command_id = command_id;
        open_duration_ms = duration_ms;
        open_start_time = millis();

        if (is_attached) {
            servo.write(SERVO_ANGLE_OPEN);
        }
        state = GATE_OPEN;
        return true;
    }

    // Call inside main loop() to handle non-blocking auto-closing
    void update(void (*on_closed_cb)()) {
        if (state == GATE_OPEN) {
            if (millis() - open_start_time >= open_duration_ms) {
                // Auto-lock after configured duration
                lockImmediate();
                if (on_closed_cb) {
                    on_closed_cb();
                }
            }
        }
    }

    ServoState getState() const {
        return state;
    }

    bool isLocked() const {
        return state == GATE_LOCKED;
    }
};

#endif // SERVO_CONTROLLER_H
