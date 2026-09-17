"use client";

import { useEffect, useState } from "react";
import { Radio, Fingerprint, HeartPulse, Monitor, Camera, Lock, Unlock, RefreshCw, AlertCircle } from "lucide-react";
import { wsClient } from "@/lib/ws";
import { api } from "@/lib/api";
import { useMode } from "@/context/ModeContext";

interface HardwareState {
  device_id: string;
  online: boolean;
  hardware_connected: boolean;
  connected_port?: string | null;
  available_ports?: string[];
  ir_presence: boolean;
  touch_pressed: boolean;
  max30102_ready: boolean;
  servo_state: string; // "LOCKED" | "OPEN"
  lcd_state: string;
  camera_online: boolean;
}

export default function HardwareStatusGrid({ initialStatus }: { initialStatus?: Partial<HardwareState> }) {
  const { mode, isLive, isDemo } = useMode();
  const [isProbing, setIsProbing] = useState(false);
  const [probeMessage, setProbeMessage] = useState<string | null>(null);

  const [status, setStatus] = useState<HardwareState>({
    device_id: "TG-001",
    online: false,
    hardware_connected: false,
    connected_port: null,
    available_ports: [],
    ir_presence: false,
    touch_pressed: false,
    max30102_ready: false,
    servo_state: "LOCKED",
    lcd_state: "WAITING",
    camera_online: true,
    ...initialStatus,
  });

  const loadStatus = () => {
    api.getDeviceStatus().then((res) => {
      setStatus((prev) => ({ ...prev, ...res }));
    }).catch(() => {});
  };

  useEffect(() => {
    loadStatus();

    const unsubscribe = wsClient.subscribe((msg) => {
      if (msg.type === "DEVICE_EVENT" && msg.state) {
        setStatus((prev) => ({ ...prev, ...msg.state }));
      } else if (msg.type === "PIPELINE_PROGRESS") {
        if (msg.stage === "LIVENESS") {
          setStatus((prev) => ({ ...prev, lcd_state: "LIVENESS" }));
        }
      }
    });

    return () => unsubscribe();
  }, []);

  const handleProbe = async () => {
    setIsProbing(true);
    setProbeMessage(null);
    try {
      const res = await api.probeDevice(status.device_id);
      setStatus((prev) => ({ ...prev, ...res.status }));
      setProbeMessage(res.message);
    } catch (e: any) {
      setProbeMessage("Error probing USB ports: " + e.message);
    } finally {
      setIsProbing(false);
    }
  };

  const isPhysicallyConnected = status.hardware_connected;
  // In demo mode we emulate online sensors, but in live mode we only treat them online if physically plugged in
  const isOnlineForMode = isDemo ? true : isPhysicallyConnected;

  const sensors = [
    {
      name: "IR Presence Detector",
      pin: "GPIO 34",
      active: isOnlineForMode && status.ir_presence,
      activeLabel: "PERSON IN FRAME",
      idleLabel: isOnlineForMode ? "MONITORING (READY)" : "DISCONNECTED (USB UNPLUGGED)",
      icon: Radio,
      activeColor: "border-success bg-success-surface text-success",
      idleColor: isOnlineForMode
        ? "border-border bg-white text-muted-foreground"
        : "border-danger/30 bg-danger-surface/20 text-muted-foreground",
    },
    {
      name: "Capacitive Touch Trigger",
      pin: "GPIO 32",
      active: isOnlineForMode && status.touch_pressed,
      activeLabel: "CONTACT ACTIVE",
      idleLabel: isOnlineForMode ? "ARMED & WAITING" : "DISCONNECTED (USB UNPLUGGED)",
      icon: Fingerprint,
      activeColor: "border-primary bg-amber-50/60 text-primary",
      idleColor: isOnlineForMode
        ? "border-border bg-white text-muted-foreground"
        : "border-danger/30 bg-danger-surface/20 text-muted-foreground",
    },
    {
      name: "MAX30102 Pulse Oximeter",
      pin: "I2C0 (21/22)",
      active: isOnlineForMode && status.max30102_ready,
      activeLabel: "SENSOR ACTIVE",
      idleLabel: isOnlineForMode ? "CALIBRATED (IDLE)" : "DISCONNECTED (USB UNPLUGGED)",
      icon: HeartPulse,
      activeColor: "border-primary bg-amber-50/60 text-primary",
      idleColor: isOnlineForMode
        ? "border-border bg-white text-muted-foreground"
        : "border-danger/30 bg-danger-surface/20 text-muted-foreground",
    },
    {
      name: "2.4\" TFT LCD Display",
      pin: "VSPI (18/23)",
      active: isOnlineForMode && status.online,
      activeLabel: `SCREEN: ${status.lcd_state}`,
      idleLabel: isOnlineForMode ? "OFFLINE" : "DISCONNECTED (USB UNPLUGGED)",
      icon: Monitor,
      activeColor: "border-border bg-surface text-foreground font-semibold",
      idleColor: isOnlineForMode
        ? "border-border bg-white text-muted-foreground"
        : "border-danger/30 bg-danger-surface/20 text-muted-foreground",
    },
    {
      name: "Physical Gate Servo",
      pin: "PWM (GPIO 25)",
      active: isOnlineForMode && status.servo_state === "OPEN",
      activeLabel: "GATE OPEN (90°)",
      idleLabel: isOnlineForMode ? "SECURED (0°)" : "LOCKED / DISCONNECTED (0°)",
      icon: status.servo_state === "OPEN" ? Unlock : Lock,
      activeColor: "border-success bg-success-surface text-success shadow-sm",
      idleColor: isOnlineForMode
        ? "border-border bg-white text-foreground"
        : "border-danger/30 bg-danger-surface/20 text-muted-foreground",
    },
    {
      name: "1080p USB Camera",
      pin: "Host USB",
      active: status.camera_online,
      activeLabel: "FEED STREAMING",
      idleLabel: "DISCONNECTED",
      icon: Camera,
      activeColor: "border-border bg-surface text-foreground font-semibold",
      idleColor: "border-border bg-white text-muted-foreground",
    },
  ];

  return (
    <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
        <div className="flex items-center space-x-2.5">
          <div
            className={`w-2.5 h-2.5 rounded-full ${
              isLive
                ? isPhysicallyConnected
                  ? "bg-emerald-600 shadow-[0_0_6px_rgba(16,185,129,0.5)]"
                  : "bg-red-500"
                : "bg-amber-500"
            }`}
          />
          <h2 className="text-xs font-mono font-bold uppercase tracking-widest text-foreground small-caps">
            Hardware Controller Telemetry & Physical Link
          </h2>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleProbe}
            disabled={isProbing}
            className="flex items-center gap-1.5 px-3 py-1 rounded bg-surface hover:bg-surface/80 border border-border text-xs font-mono text-foreground transition-colors shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isProbing ? "animate-spin text-primary" : ""}`} />
            <span>{isProbing ? "Probing USB Ports..." : "Check / Probe Connection"}</span>
          </button>

          <span className="text-[10px] font-mono px-2 py-1 rounded bg-surface border border-border text-foreground font-medium">
            Node: {status.device_id}
          </span>
        </div>
      </div>

      {/* Warning Notice if Disconnected in Live Mode */}
      {isLive && !isPhysicallyConnected && (
        <div className="p-3.5 rounded-lg bg-danger-surface/40 border border-danger/40 text-xs font-mono flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-foreground">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-danger shrink-0" />
            <span>
              <strong>Physical ESP32 is NOT connected via USB.</strong> Peripherals (IR, Touch, MAX30102, TFT, Servo) are offline.
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-[10px] text-muted-foreground">
              Plug in ESP32 USB cable and click Check Connection.
            </span>
          </div>
        </div>
      )}

      {/* Probe feedback banner */}
      {probeMessage && (
        <div className="p-2.5 rounded bg-surface border border-border text-[11px] font-mono text-muted-foreground flex items-center justify-between">
          <span>Result: {probeMessage}</span>
          <button onClick={() => setProbeMessage(null)} className="text-foreground hover:text-primary font-bold ml-2">
            ✕
          </button>
        </div>
      )}

      {/* 6 Peripheral Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {sensors.map((s, idx) => {
          const Icon = s.icon;
          const isCamera = s.name.includes("Camera");

          const cardContent = (
            <div
              key={idx}
              className={`p-3.5 rounded-lg border transition-all flex flex-col justify-between ${
                s.active ? s.activeColor : s.idleColor
              } ${isCamera ? "cursor-pointer hover:border-primary/80" : ""}`}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className="w-4 h-4 shrink-0" />
                <span className="text-[10px] font-mono opacity-80">{s.pin}</span>
              </div>
              <div>
                <p className="text-xs font-serif-display font-medium text-foreground truncate">
                  {s.name}
                </p>
                <p className="text-[10px] font-mono font-bold mt-1 tracking-tight">
                  {s.active ? s.activeLabel : s.idleLabel}
                </p>
                {isCamera && (
                  <p className="text-[9px] font-mono text-primary font-semibold mt-1">
                    Open Camera Kiosk →
                  </p>
                )}
              </div>
            </div>
          );

          if (isCamera) {
            return (
              <a key={idx} href="/verify">
                {cardContent}
              </a>
            );
          }

          return cardContent;
        })}
      </div>
    </div>
  );
}
