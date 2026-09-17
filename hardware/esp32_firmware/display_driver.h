#ifndef DISPLAY_DRIVER_H
#define DISPLAY_DRIVER_H

#include <Arduino.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include "config.h"

// Theme Colors (16-bit 565 RGB)
#define COLOR_BG            0x0842  // Dark slate #0b0f19
#define COLOR_CARD_BG       0x1084  // Card background
#define COLOR_TEXT_WHITE    0xFFFF
#define COLOR_TEXT_MUTED    0x8410
#define COLOR_PRIMARY_CYAN  0x07FF  // Cyan accent
#define COLOR_SUCCESS_GREEN 0x2FE4  // Neon green
#define COLOR_WARNING_AMBER 0xFDA0  // Amber warning
#define COLOR_DANGER_RED    0xF800  // Crimson danger

/**
 * Abstract DisplayDriver interface.
 * Decouples high-level UI states from specific display controller hardware.
 */
class DisplayDriver {
public:
    virtual ~DisplayDriver() {}
    virtual bool begin() = 0;
    virtual void clear() = 0;
    virtual void showWaiting() = 0;
    virtual void showTouchToStart() = 0;
    virtual void showStep(int step, int total, const char* label) = 0;
    virtual void showLivenessPrompt(int progress_pct, int bpm) = 0;
    virtual void showAccessGranted() = 0;
    virtual void showReviewRequired(const char* reason) = 0;
    virtual void showVerificationFailed(const char* reason) = 0;
    virtual void showDiagnostics(bool ir, bool touch, bool max30102, bool servo) = 0;
};

/**
 * Concrete implementation for 2.4" ILI9341 SPI TFT LCD Display.
 */
class ILI9341DisplayDriver : public DisplayDriver {
private:
    Adafruit_ILI9341 tft;

public:
    ILI9341DisplayDriver() : tft(PIN_TFT_CS, PIN_TFT_DC, PIN_TFT_RST) {}

    bool begin() override {
        // Initialize dedicated hardware VSPI
        SPI.begin(PIN_TFT_SCK, PIN_TFT_MISO, PIN_TFT_MOSI, PIN_TFT_CS);
        tft.begin();
        tft.setRotation(1); // Landscape mode: 320x240
        tft.fillScreen(COLOR_BG);
        return true;
    }

    void clear() override {
        tft.fillScreen(COLOR_BG);
    }

    void showWaiting() override {
        tft.fillScreen(COLOR_BG);
        
        // Header
        tft.fillRect(0, 0, 320, 40, COLOR_CARD_BG);
        tft.setTextColor(COLOR_PRIMARY_CYAN);
        tft.setTextSize(2);
        tft.setCursor(20, 12);
        tft.print("TRUST GATE");

        tft.setTextSize(1);
        tft.setTextColor(COLOR_TEXT_MUTED);
        tft.setCursor(230, 16);
        tft.print("SYS ONLINE");

        // Center card
        tft.fillRoundRect(30, 60, 260, 140, 8, COLOR_CARD_BG);
        tft.drawRoundRect(30, 60, 260, 140, 8, COLOR_PRIMARY_CYAN);

        tft.setTextColor(COLOR_TEXT_WHITE);
        tft.setTextSize(2);
        tft.setCursor(65, 100);
        tft.print("Scan Station");

        tft.setTextColor(COLOR_TEXT_MUTED);
        tft.setTextSize(1);
        tft.setCursor(95, 135);
        tft.print("Please approach device");
    }

    void showTouchToStart() override {
        tft.fillScreen(COLOR_BG);

        tft.fillRect(0, 0, 320, 40, COLOR_CARD_BG);
        tft.setTextColor(COLOR_PRIMARY_CYAN);
        tft.setTextSize(2);
        tft.setCursor(20, 12);
        tft.print("PERSON DETECTED");

        tft.fillRoundRect(30, 60, 260, 140, 8, COLOR_CARD_BG);
        tft.drawRoundRect(30, 60, 260, 140, 8, COLOR_SUCCESS_GREEN);

        tft.setTextColor(COLOR_SUCCESS_GREEN);
        tft.setTextSize(2);
        tft.setCursor(55, 95);
        tft.print("Touch to Start");

        tft.setTextColor(COLOR_TEXT_WHITE);
        tft.setTextSize(1);
        tft.setCursor(60, 135);
        tft.print("Press the capacitive button below");
    }

    void showStep(int step, int total, const char* label) override {
        tft.fillScreen(COLOR_BG);

        tft.fillRect(0, 0, 320, 40, COLOR_CARD_BG);
        tft.setTextColor(COLOR_PRIMARY_CYAN);
        tft.setTextSize(2);
        tft.setCursor(20, 12);
        tft.print("VERIFICATION");

        char step_buf[16];
        snprintf(step_buf, sizeof(step_buf), "0%d / 0%d", step, total);
        tft.setTextColor(COLOR_TEXT_MUTED);
        tft.setTextSize(2);
        tft.setCursor(220, 12);
        tft.print(step_buf);

        tft.fillRoundRect(30, 65, 260, 130, 8, COLOR_CARD_BG);
        tft.setTextColor(COLOR_TEXT_WHITE);
        tft.setTextSize(2);
        tft.setCursor(45, 105);
        tft.print(label);

        // Progress bar
        int bar_width = (step * 220) / total;
        tft.drawRect(50, 150, 220, 12, COLOR_TEXT_MUTED);
        tft.fillRect(52, 152, bar_width, 8, COLOR_PRIMARY_CYAN);
    }

    void showLivenessPrompt(int progress_pct, int bpm) override {
        tft.fillScreen(COLOR_BG);

        tft.fillRect(0, 0, 320, 40, COLOR_CARD_BG);
        tft.setTextColor(COLOR_PRIMARY_CYAN);
        tft.setTextSize(2);
        tft.setCursor(20, 12);
        tft.print("LIVENESS CHECK");

        tft.fillRoundRect(30, 60, 260, 145, 8, COLOR_CARD_BG);
        tft.drawRoundRect(30, 60, 260, 145, 8, COLOR_PRIMARY_CYAN);

        tft.setTextColor(COLOR_TEXT_WHITE);
        tft.setTextSize(2);
        tft.setCursor(50, 85);
        tft.print("Place Finger Here");

        if (bpm > 0) {
            char bpm_buf[24];
            snprintf(bpm_buf, sizeof(bpm_buf), "Pulse: %d BPM", bpm);
            tft.setTextColor(COLOR_SUCCESS_GREEN);
            tft.setTextSize(1);
            tft.setCursor(105, 120);
            tft.print(bpm_buf);
        } else {
            tft.setTextColor(COLOR_WARNING_AMBER);
            tft.setTextSize(1);
            tft.setCursor(85, 120);
            tft.print("Detecting pulse signal...");
        }

        // Progress bar
        int w = (progress_pct * 200) / 100;
        tft.drawRect(60, 155, 200, 12, COLOR_TEXT_MUTED);
        tft.fillRect(62, 157, w, 8, COLOR_PRIMARY_CYAN);
    }

    void showAccessGranted() override {
        tft.fillScreen(COLOR_BG);

        tft.fillRoundRect(20, 25, 280, 190, 10, COLOR_CARD_BG);
        tft.drawRoundRect(20, 25, 280, 190, 10, COLOR_SUCCESS_GREEN);

        tft.setTextColor(COLOR_SUCCESS_GREEN);
        tft.setTextSize(3);
        tft.setCursor(45, 55);
        tft.print("VERIFIED");

        tft.setTextColor(COLOR_TEXT_WHITE);
        tft.setTextSize(2);
        tft.setCursor(45, 105);
        tft.print("ACCESS GRANTED");

        tft.setTextColor(COLOR_TEXT_MUTED);
        tft.setTextSize(1);
        tft.setCursor(45, 155);
        tft.print("Gate opening... Please enter.");
    }

    void showReviewRequired(const char* reason) override {
        tft.fillScreen(COLOR_BG);

        tft.fillRoundRect(20, 25, 280, 190, 10, COLOR_CARD_BG);
        tft.drawRoundRect(20, 25, 280, 190, 10, COLOR_WARNING_AMBER);

        tft.setTextColor(COLOR_WARNING_AMBER);
        tft.setTextSize(2);
        tft.setCursor(40, 50);
        tft.print("REVIEW REQUIRED");

        tft.setTextColor(COLOR_TEXT_WHITE);
        tft.setTextSize(1);
        tft.setCursor(40, 95);
        tft.print(reason ? reason : "Identity requires verification");

        tft.setTextColor(COLOR_TEXT_MUTED);
        tft.setTextSize(1);
        tft.setCursor(40, 150);
        tft.print("Please proceed to the organizer desk.");
    }

    void showVerificationFailed(const char* reason) override {
        tft.fillScreen(COLOR_BG);

        tft.fillRoundRect(20, 25, 280, 190, 10, COLOR_CARD_BG);
        tft.drawRoundRect(20, 25, 280, 190, 10, COLOR_DANGER_RED);

        tft.setTextColor(COLOR_DANGER_RED);
        tft.setTextSize(2);
        tft.setCursor(40, 50);
        tft.print("VERIFY FAILED");

        tft.setTextColor(COLOR_TEXT_WHITE);
        tft.setTextSize(1);
        tft.setCursor(40, 95);
        tft.print(reason ? reason : "Access Denied");

        tft.setTextColor(COLOR_TEXT_MUTED);
        tft.setTextSize(1);
        tft.setCursor(40, 150);
        tft.print("Physical gate locked.");
    }

    void showDiagnostics(bool ir, bool touch, bool max30102, bool servo) override {
        tft.fillScreen(COLOR_BG);
        tft.setTextColor(COLOR_PRIMARY_CYAN);
        tft.setTextSize(2);
        tft.setCursor(20, 20);
        tft.print("DIAGNOSTICS");

        tft.setTextSize(1);
        tft.setTextColor(COLOR_TEXT_WHITE);

        tft.setCursor(20, 60);
        tft.printf("IR Presence:   %s", ir ? "DETECTED" : "CLEAR");

        tft.setCursor(20, 90);
        tft.printf("Touch Sensor:  %s", touch ? "ACTIVE" : "IDLE");

        tft.setCursor(20, 120);
        tft.printf("MAX30102 I2C:  %s", max30102 ? "OK" : "ERROR");

        tft.setCursor(20, 150);
        tft.printf("Servo Gate:    %s", servo ? "OPEN" : "LOCKED");
    }
};

#endif // DISPLAY_DRIVER_H
