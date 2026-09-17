# TRUST GATE: Physical Identity & Eligibility Gateway

> **An authoritative, cyber-physical identity verification and access control system integrating physical ESP32 microcontrollers, physiological liveness detection, multi-agent AI verification (Google Gemini Vision / Groq / AWS Textract), and physical turnstile servo actuation.**

---

## Table of Contents
1. [System Architecture](#1-system-architecture)
2. [Key Features](#2-key-features)
3. [Quick Start Guide](#3-quick-start-guide)
4. [Environment Configuration (.env)](#4-environment-configuration-env)
5. [Hardware Wiring & Assembly Guide](#5-hardware-wiring--assembly-guide)
6. [Flashing the ESP32 Firmware](#6-flashing-the-esp32-firmware)
7. [Operating Modes: LIVE vs DEMO](#7-operating-modes-live-vs-demo)
8. [Testing & Verification](#8-testing--verification)
9. [Judge Demonstration Pitch Guide](#9-judge-demonstration-pitch-guide)
10. [Repository Structure](#10-repository-structure)

---

## 1. System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│             FRONTEND: Next.js 14 Web Application (Port 3000)                │
│  • Editorial Serif Design System (Playfair Display / Source Sans / Mono)    │
│  • Persistent Top Mode Switch: [ ● LIVE GATEWAY | ○ DEMO MODE ]             │
│  • Real-Time Multi-Sensor Waveform Graph (100 Hz Continuous PPG, IR, Touch) │
│  • Guided Verification Kiosk (/verify) with Step Guidance & Voice Prompts   │
│  • Organizer Review Dossier (/review) with Side-by-Side Conflict Inspection │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ WebSocket (/ws/live) & REST API
┌──────────────────────────────────────▼──────────────────────────────────────┐
│              BACKEND: FastAPI Orchestrator (Port 8000)                      │
│  • 7 Specialized AI Agents returning unified AgentResult contract          │
│  • Dual-LLM Engine: Groq (Llama 3.3 70B) + Google Gemini Failover           │
│  • Document Extraction: Google Gemini Multimodal Vision / AWS Textract      │
│  • Credential Checksum: Verhoeff D5 algorithm (Aadhaar) + RTO State Regex   │
│  • Biometric Face Verification: 128D Deep Embeddings & Cosine Similarity     │
│  • Deterministic Safety Policy: Ambiguity defaults to REVIEW (Never unlocks)│
│  • Hardware Guard: Session-scoped anti-replay protection (command_id)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ USB Serial (115200 baud) or Virtual
┌──────────────────────────────────────▼──────────────────────────────────────┐
│            HARDWARE: ESP32 Microcontroller Node (TG-001)                    │
│  • IR Presence Proximity Sensor (Input-Only GPIO 34)                        │
│  • Capacitive Touch Trigger Button (TTP223 on GPIO 32)                      │
│  • MAX30102 Pulse Oximeter Sensor (Hardware I2C0: GPIO 21 / 22)             │
│  • 2.4" SPI TFT LCD Display (ILI9341 on Dedicated VSPI: 18/23/19/5/27/4)    │
│  • Physical Turnstile Barrier (LEDC PWM 50Hz on Dedicated GPIO 25)          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Features

- **Multi-Modal Verification**: Validates identity across physical document image, live webcam biometric selfie, and physiological capillary blood pulse.
- **Option A "Serif / Editorial" UI**: Warm ivory (`#FAFAF8`), rich black (`#1A1A1A`), burnished gold (`#B8860B`), classical Roman numerals (**I**–**VIII**), and publication-grade verdict seals.
- **Continuous Multi-Sensor Waveform Oscilloscope**: Canvas visualizer rendering live PPG pulse wave with dicrotic notch, IR proximity distance curve, and touch contact frequency at 100 Hz.
- **Dual-LLM with Automatic Quota Failover**: Dispatches explanation prompts to **Groq** for sub-300ms speed. If Groq encounters rate limits or quota exhaustion (HTTP 429), it automatically cascades to **Google Gemini** without human intervention.
- **Bogus ID & Forgery Detection**:
  - **Verhoeff D5 Checksum**: Instant mathematical verification of 12-digit Aadhaar numbers (catches randomly generated fake IDs in 0.001 ms).
  - **RTO State Regex**: Verifies authentic Indian Driving License patterns.
  - **Error Level Analysis (ELA)**: Computer vision algorithm detecting digital manipulation and photoshopped text.
- **Strict Hardware Safety Policy**: Default locked (0°). The physical turnstile servo can only be commanded open via a single-use UUIDv4 `command_id` generated upon authoritative `PASS`. Automatically re-locks after 5000 ms.

---

## 3. Quick Start Guide

### Prerequisites
- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.13)
- **Node.js 18+** (Node.js 20 LTS recommended)
- **Webcam**: Built-in laptop webcam or USB webcam
- **ESP32 (Optional for full physical setup)**: Can run in Virtual Simulator / Demo mode without any hardware attached.

---

### Step 1: Clone & Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
```

---

### Step 2: Setup Frontend

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Build production bundle
npm run build
```

---

### Step 3: Launch Both Services

**Terminal 1 — FastAPI Backend**:
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend API will run at `http://localhost:8000` (OpenAPI Swagger Docs at `http://localhost:8000/docs`).*

**Terminal 2 — Next.js Frontend**:
```bash
cd frontend
npm start
# (Or npm run dev for hot-reloading development)
```
*Frontend Web Kiosk will run at `http://localhost:3000`.*

---

## 4. Environment Configuration (.env)

Create a `.env` file in `backend/.env` (reference `backend/.env.example`):

```env
# ==========================================================
# TRUST GATE: Backend Environment Configuration
# ==========================================================

# 1. Dual-LLM Reasoning Engine (Groq + Gemini Auto-Failover)
# Get free Groq API key: https://console.groq.com
GROQ_API_KEY="gsk_your_groq_key_here"

# Get Google Gemini / GCP API key: https://aistudio.google.com
GEMINI_API_KEY="AIzaSy_your_gemini_key_here"

# Models
GROQ_MODEL="llama-3.3-70b-versatile"
GEMINI_MODEL="gemini-1.5-flash"

# 2. Document OCR Extraction Engine ("GEMINI", "TEXTRACT", or "AUTO")
# Set to "GEMINI" to use GCP / Google Gemini Multimodal Vision (Recommended)
OCR_PROVIDER="GEMINI"

# 3. AWS Textract (Optional — only if you prefer AWS over Google Cloud)
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
AWS_REGION="us-east-1"

# 4. Hardware Serial Port Configuration
# Set to "AUTO" to automatically detect ESP32 on USB COM ports, or set e.g. "COM3"
SERIAL_PORT="AUTO"
SERIAL_BAUD_RATE=115200
GATE_OPEN_DURATION_MS=5000

# 5. Security Credentials
JWT_SECRET="trustgate-secret-key-change-in-production-2026"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"
```

> [!NOTE]
> If external API keys are omitted, the system seamlessly operates using its built-in **deterministic local engine** so you can run the entire prototype offline!

---

## 5. Hardware Wiring & Assembly Guide

### Verified ESP32 Pinout (Zero GPIO Conflicts)

All pins are centralized in [`hardware/esp32_firmware/config.h`](file:///a:/trustgate/hardware/esp32_firmware/config.h) and verified against ESP32 strapping pins:

| Peripheral Module | ESP32 GPIO Pin | Direction | Bus / Protocol | Wiring Notes |
|---|---|---|---|---|
| **IR Presence Sensor** | `GPIO 34` | Input | Digital In (GPI) | Connect sensor `OUT`. Input-only pin. Active LOW when obstacle detected. |
| **Capacitive Touch** | `GPIO 32` | Input | Digital In | Connect TTP223 module `OUT`. Active HIGH on finger touch. |
| **MAX30102 SDA** | `GPIO 21` | In / Out | Hardware I2C0 | Connect `SDA`. Requires 4.7kΩ pull-up to 3.3V. |
| **MAX30102 SCL** | `GPIO 22` | Output | Hardware I2C0 | Connect `SCL` (400 kHz Fast Mode). Requires 4.7kΩ pull-up. |
| **TFT SPI SCK** | `GPIO 18` | Output | VSPI Clock | Connect ILI9341 `SCK / CLK`. Dedicated hardware VSPI clock. |
| **TFT SPI MOSI** | `GPIO 23` | Output | VSPI MOSI | Connect ILI9341 `MOSI / SDI`. Master-Out-Slave-In. |
| **TFT SPI MISO** | `GPIO 19` | Input | VSPI MISO | Connect ILI9341 `MISO / SDO` (optional). |
| **TFT CS** | `GPIO 5` | Output | SPI Chip Select | Connect ILI9341 `CS`. Active LOW. |
| **TFT DC / RS** | `GPIO 27` | Output | Digital Out | Connect ILI9341 `DC / RS` (Data / Command selector). |
| **TFT RST** | `GPIO 4` | Output | Digital Out | Connect ILI9341 `RST` (Hardware reset). |
| **Gate Servo Signal** | `GPIO 25` | Output | LEDC PWM (50Hz) | Dedicated 50Hz PWM signal. Completely isolated from SPI clock. |
| **Power Supply** | `VIN / 5V` | Power | DC Power | Connect to 5V 2A external power rail (shared ground with ESP32). |
| **Common Ground** | `GND` | Ground | Ground | Common ground rail connecting ESP32, TFT, Servo, and Sensors. |

> [!CAUTION]
> **Power Isolation Warning**: Do NOT power the SG90 / MG996R servo directly from the ESP32 3.3V rail. Power the servo from the 5V power supply or USB 5V rail to prevent voltage brownouts during servo motor movement.

---

## 6. Flashing the ESP32 Firmware

1. Open the Arduino IDE (v2.0+) or PlatformIO.
2. Install the required libraries via **Library Manager**:
   - `Adafruit GFX Library`
   - `Adafruit ILI9341`
   - `ESP32Servo`
   - `ArduinoJson` (v6.21+)
3. Open [`hardware/esp32_firmware/trust_gate_esp32.ino`](file:///a:/trustgate/hardware/esp32_firmware/trust_gate_esp32.ino).
4. Select Board: **ESP32 Dev Module**.
5. Connect your ESP32 to your computer via micro-USB / USB-C cable and select the port (e.g. `COM3`).
6. Click **Upload**.
7. Open the Serial Monitor at **115200 baud**. You will see:
   ```text
   [INIT] TRUST GATE Hardware Controller v1.0.0
   [CONFIG] Hardware pin validation passed. Zero GPIO conflicts.
   [READY] ESP32 listening for serial commands.
   ```

---

## 7. Operating Modes: LIVE vs DEMO

A persistent toggle is located in the top navigation bar across all pages:

### 1. `LIVE GATEWAY` Mode
- **Authentic Physical Telemetry**: Strictly verifies whether an ESP32 is physically plugged into a USB COM port.
- **Disconnected Safeguard**: If no physical board is plugged in, the waveform flatlines, sensor cards read `DISCONNECTED (USB UNPLUGGED)`, and a **`[ Check / Probe Connection ]`** button scans all system COM ports.
- **Webcam & Sensors**: Uses your laptop's live built-in webcam for real-time document capture and face selfie.
- **Admin Review Queue**: Monitors real flagged physical entrance sessions.

### 2. `DEMO MODE` Mode
- **Fast-Track Demonstration**: Renders realistic multi-harmonic analog waveforms and lets you demonstrate all 6 PRD verification scenarios (A through F) with 1 click.
- **Kiosk Presets**: Provides one-click buttons (`Simulate Valid Participant`, `Simulate Duplicate ID`) to test the complete evaluation pipeline in seconds.
- **Admin Review Fallback**: Includes a `Populate Demo Review Case` button to test organizer approvals and physical gate fallback without touching hardware.

---

## 8. Testing & Verification

### Run Automated Unit & Integration Tests (pytest)
```bash
cd backend
python -m pytest tests/test_verification_pipeline.py -v
```
*Executes all 8 backend verification tests across scenarios, hashing, and decision rules.*

### Run Live End-to-End Test Suite (13 Test Suites)
```bash
cd backend
python tests/test_live_e2e.py
```
*Executes the complete 13-stage verification suite against the running server:*
- Health check & telemetry
- IR sensor triggers & session initialization
- MAX30102 pulse telemetry recording
- Scenarios A, B, C, D, E, F execution
- Admin manual review & audit logging
- Hardware policy anti-replay validation

---

## 9. Judge Demonstration Pitch Guide

### 2-Minute Presentation Script for Judges:

#### 1. The Hook (30s)
> *"Judges, conventional identity verification at events, airports, and secure venues relies on human volunteers glancing at ID cards. This leads to fake IDs, borrowed cards, duplicate entries, and severe bottlenecks.
> **TRUST GATE** is a real, working cyber-physical security gateway that combines physical ESP32 hardware and physiological sensors with an AI multi-agent verification pipeline to authoritatively control a physical turnstile servo."*

#### 2. The Live UI & Sensor Waveforms (30s)
> *"Take a look at our dispatch center at `localhost:3000`. You can see our **Option A Editorial Serif design system** and persistent **LIVE vs DEMO** toggle.
> Notice our real-time **Multi-Sensor Waveform Graph**: It plots analog telemetry in real time—the MAX30102 PPG pulse wave with its dicrotic notch, the IR proximity curve, and the capacitive touch baseline."*

#### 3. Demonstrate Scenario A: Genuine Participant (30s)
1. Go to `/verify` (Verification Kiosk).
2. Show the judges the **3-step guided flow** with on-screen visual alignment guides and voice prompts.
3. Click **Scenario A (Genuine Participant)** on the Demo Hub (`/demo`).
4. Watch the **AI Evidence Dossier** execute:
   - Extraction Agent (Google Gemini Vision / AWS Textract): Name & DOB extracted (`PASS`).
   - Forensics Agent: Zero ELA compression tampering detected (`PASS`).
   - Identity Matching Agent: Deep face embedding similarity at 95% (`PASS`).
   - Liveness Agent: MAX30102 pulse signal confirms living human at 74 BPM (`PASS`).
5. Point to the **Turnstile Servo**: The physical arm swings to 90° (`ACCESS GRANTED`) and auto-locks after 5 seconds.

#### 4. Demonstrate Fake ID Catch & Admin Review (30s)
> *"Now, what if someone presents a fake ID or borrows a friend's card?"*
1. Trigger **Scenario B (Reused ID)** or **Scenario C (Tampered Forensics)**.
2. Show that the turnstile **stays strictly locked (0°)**—the AI safely refuses to open.
3. Switch to **Admin Review (`/review`)**:
   - Show the flagged session with side-by-side evidence inspection.
   - Enter reviewer name, type an audit reason, and click **Approve & Actuate Gate** or **Reject Access** to demonstrate immutable audit logging.

---

## 10. Repository Structure

```text
trustgate/
├── backend/
│   ├── app/
│   │   ├── adapters/          # Face recognition, Gemini Vision, AWS Textract, Groq/Gemini LLM
│   │   ├── agents/            # 7 specialized AI verification agents
│   │   ├── core/              # Verhoeff checksum algorithm, security hashing, image utils
│   │   ├── models/            # SQLAlchemy database models (Participant, Session, Evidence)
│   │   ├── routers/           # FastAPI REST & WebSocket endpoints
│   │   ├── schemas/           # Pydantic request/response contracts
│   │   ├── services/          # DecisionEngine, HardwarePolicy, DeviceBridge, Orchestrator
│   │   ├── config.py          # Centralized configuration & environment settings
│   │   ├── database.py        # Database engine (PostgreSQL with SQLite auto-fallback)
│   │   └── main.py            # FastAPI application entrypoint
│   ├── tests/                 # Pytest integration tests & live E2E test scripts
│   ├── .env.example           # Environment template with Groq, Gemini, and hardware config
│   └── requirements.txt       # Python dependencies
│
├── frontend/
│   ├── app/                   # Next.js 14 App Router
│   │   ├── page.tsx           # Command Center Dashboard with Waveform Graph
│   │   ├── verify/page.tsx    # Guided Verification Kiosk with Camera & Voice Prompts
│   │   ├── review/page.tsx    # Organizer Admin Review Queue with Evidence Dossier
│   │   ├── demo/page.tsx      # Demo Control Center with Scenarios A–F
│   │   └── simulator/page.tsx # Virtual Hardware Simulator with Animated Turnstile
│   ├── components/            # UI components (SensorWaveformGraph, HardwareStatusGrid, etc.)
│   ├── context/               # Global ModeContext (LIVE vs DEMO state)
│   ├── lib/                   # API client & WebSocket streaming client
│   └── tailwind.config.ts     # Option A Editorial Serif design tokens & fonts
│
├── hardware/
│   └── esp32_firmware/        # C++ Arduino firmware with verified zero-conflict pinouts
│
├── .gitignore                 # Root gitignore for Python, Node.js, and secrets
└── README.md                  # Comprehensive project documentation
```

---

## License & Credits
Built for Hackingly AI 2026. Designed and engineered as a production-grade cyber-physical prototype.
