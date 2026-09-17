"use client";

import { useEffect, useState } from "react";
import { Cpu, Radio, Fingerprint, HeartPulse, Lock, Unlock, RefreshCw, Terminal, Sliders } from "lucide-react";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/ws";
import SensorWaveformGraph from "@/components/SensorWaveformGraph";

export default function SimulatorPage() {
  const [deviceStatus, setDeviceStatus] = useState<any>({
    online: true,
    ir_presence: false,
    touch_pressed: false,
    max30102_ready: true,
    servo_state: "LOCKED",
    lcd_state: "WAITING",
  });
  const [eventLogs, setEventLogs] = useState<string[]>([]);

  useEffect(() => {
    api.getDeviceStatus().then(setDeviceStatus).catch(() => {});

    const unsubscribe = wsClient.subscribe((msg) => {
      if (msg.type === "DEVICE_EVENT") {
        if (msg.state) setDeviceStatus(msg.state);
        const line = `[${new Date().toLocaleTimeString()}] EVENT: ${msg.event} | DATA: ${JSON.stringify(
          msg.data || {}
        )}`;
        setEventLogs((prev) => [line, ...prev.slice(0, 25)]);
      }
    });

    return () => unsubscribe();
  }, []);

  const triggerEvent = async (event: string, extra = {}) => {
    try {
      await api.sendDeviceEvent(event, "TG-001", extra);
    } catch (e: any) {
      console.error("Event trigger error:", e);
    }
  };

  const isGateOpen = deviceStatus.servo_state === "OPEN";

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-surface border border-border text-foreground">
              VIRTUAL BENCHMARK TESTBED
            </span>
          </div>
          <h1 className="text-2xl font-serif-display font-black text-foreground tracking-tight flex items-center gap-2.5">
            <Cpu className="w-6 h-6 text-primary" />
            ESP32 Hardware Simulation Laboratory
          </h1>
          <p className="text-xs text-muted-foreground font-mono">
            Interactive testbed for pin validation, sensor telemetry synthesis, TFT display, and physical servo actuation
          </p>
        </div>

        <button
          onClick={() => triggerEvent("RESET")}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-md bg-surface border border-border text-xs font-mono text-foreground hover:bg-surface/70 transition-colors self-start"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reset Hardware State
        </button>
      </div>

      {/* Live Waveform Monitor */}
      <SensorWaveformGraph height={180} />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Interactive Sensor Controls */}
        <div className="lg:col-span-6 space-y-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-border">
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-foreground small-caps">
                Interactive Sensor Stimulus Controls
              </h2>
              <span className="text-[10px] font-mono text-muted-foreground">GPIO Direct Injection</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              {/* IR Presence Sensor Button */}
              <button
                onClick={() =>
                  triggerEvent("PERSON_DETECTED", {
                    detected: !deviceStatus.ir_presence,
                    distance_cm: 42.0,
                  })
                }
                className={`p-4 rounded-xl border text-left flex items-start space-x-3 transition-all ${
                  deviceStatus.ir_presence
                    ? "bg-success-surface border-success text-success font-semibold"
                    : "bg-surface/60 border-border hover:bg-white text-foreground"
                }`}
              >
                <Radio className="w-5 h-5 text-success mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs font-serif-display font-bold text-foreground">IR Sensor (GPIO 34)</p>
                  <p className="text-[11px] text-muted-foreground font-sans mt-0.5">
                    {deviceStatus.ir_presence ? "Person in frame (Triggered)" : "Simulate participant arrival"}
                  </p>
                </div>
              </button>

              {/* Touch Button */}
              <button
                onClick={() => triggerEvent("TOUCH_PRESSED")}
                className={`p-4 rounded-xl border text-left flex items-start space-x-3 transition-all ${
                  deviceStatus.touch_pressed
                    ? "bg-amber-50 border-primary text-primary font-semibold"
                    : "bg-surface/60 border-border hover:bg-white text-foreground"
                }`}
              >
                <Fingerprint className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs font-serif-display font-bold text-foreground">Touch Button (GPIO 32)</p>
                  <p className="text-[11px] text-muted-foreground font-sans mt-0.5">
                    Simulate capacitive fingertip contact
                  </p>
                </div>
              </button>

              {/* MAX30102 Liveness */}
              <button
                onClick={() =>
                  triggerEvent("LIVENESS_RESULT", {
                    pulse_detected: true,
                    signal_quality: 0.94,
                    bpm: 74.0,
                    duration_ms: 5000,
                  })
                }
                className="p-4 rounded-xl border bg-surface/60 border-border hover:bg-white text-foreground text-left flex items-start space-x-3 transition-all sm:col-span-2"
              >
                <HeartPulse className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs font-serif-display font-bold text-foreground">
                    MAX30102 Pulse Oximeter (I2C 21/22)
                  </p>
                  <p className="text-[11px] text-muted-foreground font-sans mt-0.5">
                    Inject physiological 74 BPM heartbeat pulse waveform and completed 5-second sample
                  </p>
                </div>
              </button>
            </div>
          </div>

          {/* Physical Gate Arm Graphic Animation */}
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4 font-mono">
            <div className="flex items-center justify-between pb-2 border-b border-border">
              <h2 className="text-xs font-bold uppercase text-foreground small-caps">
                Turnstile Servo Actuator (PWM GPIO 25)
              </h2>
              <span
                className={`text-xs font-bold px-2.5 py-0.5 rounded border ${
                  isGateOpen
                    ? "bg-success-surface text-success border-success/40"
                    : "bg-surface text-muted-foreground border-border"
                }`}
              >
                {isGateOpen ? "UNLOCKED / OPEN (90°)" : "SECURED / LOCKED (0°)"}
              </span>
            </div>

            {/* Precision Gate Visualizer */}
            <div className="h-44 bg-[#FAF8F5] rounded-xl border border-border flex items-center justify-center relative overflow-hidden shadow-inner">
              {/* Turnstile Base */}
              <div className="absolute left-1/4 w-12 h-28 bg-white border-2 border-border rounded-lg flex flex-col items-center justify-center z-10 shadow-sm">
                <div className="w-3 h-3 rounded-full bg-primary mb-2" />
                <span className="text-[9px] font-mono text-muted-foreground">PIVOT</span>
              </div>

              {/* Rotating Arm */}
              <div
                className="absolute left-[calc(25%+24px)] w-48 h-3 bg-gradient-to-r from-primary to-amber-700 rounded-r-full shadow-md transition-transform duration-700 ease-in-out origin-left flex items-center justify-end pr-2 z-20"
                style={{
                  transform: isGateOpen ? "rotate(-90deg)" : "rotate(0deg)",
                }}
              >
                <div className="w-2 h-2 rounded-full bg-white/70" />
              </div>

              {/* Turnstile Exit Post */}
              <div className="absolute right-1/4 w-4 h-28 bg-white border-2 border-border rounded-lg flex items-center justify-center shadow-sm">
                <span className="text-[8px] text-muted-foreground transform -rotate-90 font-mono">BARRIER</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Virtual 2.4" TFT LCD Screen Representation */}
        <div className="lg:col-span-6 space-y-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4 font-mono">
            <div className="flex items-center justify-between pb-2 border-b border-border">
              <h2 className="text-xs font-bold uppercase text-foreground small-caps">
                Virtual 2.4" TFT LCD Screen (320x240)
              </h2>
              <span className="text-[10px] text-muted-foreground">Driver: ILI9341 (VSPI Pins 18/23/19)</span>
            </div>

            {/* Virtual TFT Bezel */}
            <div className="p-4 bg-[#1A1A1A] rounded-2xl border-4 border-[#333333] shadow-2xl flex items-center justify-center">
              <div className="w-[320px] h-[240px] bg-[#0A0D14] border border-cyan-500/30 rounded-lg p-3.5 flex flex-col justify-between select-none relative overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
                  <span className="text-xs font-bold text-white tracking-wider font-serif-display">TRUST GATE</span>
                  <span className="text-[10px] text-emerald-400 font-mono">ONLINE</span>
                </div>

                {/* Body Content based on lcd_state */}
                <div className="my-auto text-center space-y-2">
                  {deviceStatus.lcd_state === "WAITING" && (
                    <>
                      <h3 className="text-lg font-bold text-white font-serif-display">Scan Station</h3>
                      <p className="text-xs text-slate-400">Please approach the turnstile</p>
                      <div className="text-[10px] text-primary animate-pulse mt-2">
                        ● SENSORS MONITORING
                      </div>
                    </>
                  )}

                  {deviceStatus.lcd_state === "TOUCH_TO_START" && (
                    <>
                      <h3 className="text-lg font-bold text-emerald-400">PERSON DETECTED</h3>
                      <p className="text-xs text-white">Touch Button to Start</p>
                      <div className="text-[10px] text-emerald-400 font-bold mt-2">
                        ● READY FOR SCAN
                      </div>
                    </>
                  )}

                  {deviceStatus.lcd_state === "SCANNING" && (
                    <>
                      <h3 className="text-base font-bold text-amber-300">VERIFICATION</h3>
                      <p className="text-xs text-slate-200">Starting Camera Capture...</p>
                      <div className="w-48 h-2 bg-slate-800 rounded-full mx-auto overflow-hidden mt-2">
                        <div className="w-1/3 h-full bg-primary animate-pulse" />
                      </div>
                    </>
                  )}

                  {deviceStatus.lcd_state === "LIVENESS" && (
                    <>
                      <h3 className="text-base font-bold text-amber-300">LIVENESS CHECK</h3>
                      <p className="text-xs text-white">Place finger on MAX30102</p>
                      <p className="text-[11px] text-rose-400 font-bold">Measuring pulse wave...</p>
                    </>
                  )}

                  {deviceStatus.lcd_state === "ACCESS_GRANTED" && (
                    <>
                      <h3 className="text-xl font-black text-emerald-400 font-serif-display">✓ VERIFIED</h3>
                      <p className="text-xs font-bold text-white">ACCESS GRANTED</p>
                      <p className="text-[10px] text-slate-400">Gate open. Please proceed.</p>
                    </>
                  )}

                  {deviceStatus.lcd_state === "REVIEW_REQUIRED" && (
                    <>
                      <h3 className="text-lg font-bold text-amber-400">⚠ REVIEW REQUIRED</h3>
                      <p className="text-xs text-white">Please see registration desk</p>
                      <p className="text-[10px] text-slate-400">Gate remains locked</p>
                    </>
                  )}

                  {deviceStatus.lcd_state === "VERIFICATION_FAILED" && (
                    <>
                      <h3 className="text-lg font-bold text-red-500">✕ ACCESS DENIED</h3>
                      <p className="text-xs text-white">Verification Failed</p>
                      <p className="text-[10px] text-slate-400">Gate locked</p>
                    </>
                  )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between text-[9px] text-slate-500 border-t border-white/10 pt-1">
                  <span>DEV: TG-001</span>
                  <span>STATE: {deviceStatus.lcd_state}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Live Serial Event Log Console */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-2 font-mono text-xs">
            <div className="flex items-center justify-between text-muted-foreground border-b border-border pb-2">
              <span className="flex items-center gap-1.5 text-foreground font-bold">
                <Terminal className="w-3.5 h-3.5 text-primary" />
                Serial Telemetry Stream (115200 baud)
              </span>
              <span className="text-[10px] text-muted-foreground">{eventLogs.length} events</span>
            </div>

            <div className="h-32 overflow-y-auto bg-surface/80 p-3 rounded-lg border border-border text-[11px] text-foreground space-y-1">
              {eventLogs.length === 0 ? (
                <span className="text-muted-foreground">Awaiting hardware serial events...</span>
              ) : (
                eventLogs.map((log, i) => (
                  <div key={i} className="truncate">
                    {log}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
