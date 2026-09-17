#ifndef TRUST_GATE_CONFIG_H
#define TRUST_GATE_CONFIG_H

#include <Arduino.h>

// ============================================================================
// TRUST GATE HARDWARE CONFIGURATION
// Centrally defines all board pins, timing parameters, and device identities.
// ============================================================================

#define DEVICE_ID               "TG-001"
#define SERIAL_BAUD_RATE        115200

// ----------------------------------------------------------------------------
// GPIO PIN ASSIGNMENTS (ESP32 DevKit v1 / ESP-WROOM-32)
// Every pin is validated to prevent overlaps or invalid direction usage.
// ----------------------------------------------------------------------------

// IR Presence Sensor (Input-only GPI pin)
#define PIN_IR_SENSOR           34    // GPI pin - input only, no internal pull-ups

// Capacitive Touch Button (Touch9 / Digital In)
#define PIN_TOUCH_BUTTON        32    // Active HIGH digital out from TTP223 or touchRead()

// MAX30102 Pulse Oximeter & Heart-Rate Sensor (Hardware I2C0)
#define PIN_I2C_SDA             21    // I2C Data
#define PIN_I2C_SCL             22    // I2C Clock
#define I2C_CLOCK_SPEED         400000 // 400 kHz fast mode

// 2.4" SPI TFT LCD Display (Hardware VSPI Bus)
#define PIN_TFT_SCK             18    // VSPI Clock
#define PIN_TFT_MOSI            23    // VSPI Master-Out-Slave-In
#define PIN_TFT_MISO            19    // VSPI Master-In-Slave-Out (optional)
#define PIN_TFT_CS              5     // Chip Select (Safe boot pin with pull-up)
#define PIN_TFT_DC              27    // Data / Command
#define PIN_TFT_RST             4     // Hardware Reset
#define TFT_WIDTH               320
#define TFT_HEIGHT              240

// Physical Gate Servo Motor (Dedicated Hardware PWM / LEDC)
#define PIN_SERVO_GATE          25    // Dedicated PWM output (Isolated from SPI/I2C)
#define SERVO_LEDC_CHANNEL      0
#define SERVO_LEDC_FREQ         50    // 50 Hz standard servo frequency
#define SERVO_LEDC_RES          16    // 16-bit timer resolution
#define SERVO_ANGLE_LOCKED      0     // Gate closed / locked (0 degrees)
#define SERVO_ANGLE_OPEN        90    // Gate fully open (90 degrees)
#define GATE_OPEN_DURATION_MS   5000  // Automatic re-lock timeout (milliseconds)

// Liveness Detection Thresholds
#define LIVENESS_SAMPLE_WINDOW_MS 4000 // Minimum contact time required
#define LIVENESS_MIN_QUALITY_PCT  65   // Minimum SNR quality percentage

// ----------------------------------------------------------------------------
// COMPILE-TIME PIN CONFLICT VALIDATION GUARD
// ----------------------------------------------------------------------------
#if (PIN_SERVO_GATE == PIN_TFT_SCK)  || (PIN_SERVO_GATE == PIN_TFT_MOSI) || \
    (PIN_SERVO_GATE == PIN_TFT_CS)   || (PIN_SERVO_GATE == PIN_TFT_DC)   || \
    (PIN_SERVO_GATE == PIN_TFT_RST)  || (PIN_SERVO_GATE == PIN_I2C_SDA)  || \
    (PIN_SERVO_GATE == PIN_I2C_SCL)  || (PIN_SERVO_GATE == PIN_IR_SENSOR)|| \
    (PIN_SERVO_GATE == PIN_TOUCH_BUTTON)
  #error "FATAL CONFIG ERROR: PIN_SERVO_GATE conflicts with another peripheral!"
#endif

#if (PIN_IR_SENSOR == PIN_TFT_SCK)   || (PIN_IR_SENSOR == PIN_TFT_MOSI)  || \
    (PIN_IR_SENSOR == PIN_I2C_SDA)   || (PIN_IR_SENSOR == PIN_I2C_SCL)   || \
    (PIN_IR_SENSOR == PIN_TOUCH_BUTTON)
  #error "FATAL CONFIG ERROR: PIN_IR_SENSOR duplicate GPIO assignment detected!"
#endif

#if (PIN_I2C_SDA == PIN_I2C_SCL) || (PIN_TFT_SCK == PIN_TFT_MOSI)
  #error "FATAL CONFIG ERROR: Bus data and clock lines share the same GPIO!"
#endif

// ----------------------------------------------------------------------------
// RUNTIME HARDWARE VALIDATION FUNCTION
// ----------------------------------------------------------------------------
static inline bool validateHardwareConfiguration() {
    const int all_pins[] = {
        PIN_IR_SENSOR, PIN_TOUCH_BUTTON, PIN_I2C_SDA, PIN_I2C_SCL,
        PIN_TFT_SCK, PIN_TFT_MOSI, PIN_TFT_MISO, PIN_TFT_CS,
        PIN_TFT_DC, PIN_TFT_RST, PIN_SERVO_GATE
    };
    const size_t num_pins = sizeof(all_pins) / sizeof(all_pins[0]);

    for (size_t i = 0; i < num_pins; i++) {
        for (size_t j = i + 1; j < num_pins; j++) {
            if (all_pins[i] == all_pins[j]) {
                Serial.printf("[FATAL] Duplicate GPIO assignment detected at indices %u and %u (GPIO: %d)\n", i, j, all_pins[i]);
                return false;
            }
        }
    }
    return true;
}

#endif // TRUST_GATE_CONFIG_H
