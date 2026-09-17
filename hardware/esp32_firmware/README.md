# TRUST GATE: ESP32 Hardware Firmware & Wiring Guide

This directory contains the production-ready C++ firmware for the **Trust Gate Physical Verification Gateway**.

---

## 1. Verified Hardware Pinout Table (Zero GPIO Conflicts)

| Peripheral | Board Pin | Direction | Protocol | Wiring / Electrical Notes |
|---|---|---|---|---|
| **IR Presence Sensor** | `GPIO 34` | Input | Digital In (GPI) | Input-only ESP32 pin. Connect sensor OUT pin. (Active LOW on obstacle). |
| **Capacitive Touch** | `GPIO 32` | Input | Digital In | Connect TTP223 capacitive touch sensor OUT pin. (Active HIGH on touch). |
| **MAX30102 SDA** | `GPIO 21` | Bidirectional | I2C0 Data | Standard I2C Data line with 4.7kΩ pull-up to 3.3V. |
| **MAX30102 SCL** | `GPIO 22` | Output | I2C0 Clock | Standard I2C Clock line with 4.7kΩ pull-up to 3.3V (400kHz). |
| **TFT SPI SCK** | `GPIO 18` | Output | VSPI Clock | Dedicated hardware VSPI clock line for 2.4" TFT LCD. |
| **TFT SPI MOSI** | `GPIO 23` | Output | VSPI MOSI | Dedicated hardware VSPI MOSI data line. |
| **TFT SPI MISO** | `GPIO 19` | Input | VSPI MISO | Optional. Connect to display SDO/MISO pin. |
| **TFT CS** | `GPIO 5` | Output | SPI Chip Select | Active LOW chip select. Safe boot pin with internal pull-up. |
| **TFT DC / RS** | `GPIO 27` | Output | Digital Out | Data/Command selector pin. |
| **TFT RST** | `GPIO 4` | Output | Digital Out | Active LOW hardware reset. |
| **Gate Servo Signal** | `GPIO 25` | Output | LEDC PWM (50Hz) | Dedicated 50Hz PWM signal for servo arm. Completely isolated from SPI bus. |
| **Power Supply** | `5V / VIN` | Power | DC Power | Connect to 5V 2A external power supply (shared ground with ESP32). |
| **Common Ground** | `GND` | Ground | Ground | Common ground rail for ESP32, TFT, Servo, and Sensors. |

---

## 2. Hardware Safety Features

1. **Hardware Replay Protection**:
   Commands (`OPEN_GATE`) include unique UUIDv4 `command_id` values. Replayed serial packets are detected and discarded.
2. **Auto-Lock Interval**:
   The gate servo automatically drives from 90° (open) back to 0° (locked) after 5000ms using a non-blocking internal timer.
3. **Default Locked State**:
   On boot, brownout, or serial disconnect, the servo immediately returns to and holds the locked position (0°).
4. **Compile-Time & Startup Assertion**:
   Firmware verifies at both compile time (`#error`) and boot time (`validateHardwareConfiguration()`) that no duplicate GPIOs exist.

---

## 3. Required Arduino Libraries

Install the following libraries via Arduino IDE Library Manager or PlatformIO:

- **`Adafruit GFX Library`** (v1.11+)
- **`Adafruit ILI9341`** (v1.6+)
- **`ESP32Servo`** (v3.0+)
- **`ArduinoJson`** (v6.21+)

---

## 4. Flashing Instructions

1. Open `trust_gate_esp32.ino` in the Arduino IDE.
2. Select Board: **ESP32 Dev Module** (or your specific ESP32 board).
3. Set CPU Frequency to **240MHz**.
4. Set Flash Frequency to **80MHz**.
5. Connect your ESP32 via USB and select the corresponding COM port.
6. Click **Upload**.
7. Open Serial Monitor at **115200 baud** to view startup self-test logs and `DEVICE_READY` handshake.
