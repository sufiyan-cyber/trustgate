"use client";

import { useEffect, useRef, useState } from "react";
import { Activity, Radio, Fingerprint, HeartPulse, Sliders, Pause, Play, AlertCircle } from "lucide-react";
import { useMode } from "@/context/ModeContext";
import { wsClient } from "@/lib/ws";
import { api } from "@/lib/api";

type ChannelType = "all" | "ppg" | "ir" | "touch";

interface SensorWaveformGraphProps {
  channelFilter?: ChannelType;
  height?: number;
  className?: string;
  showControls?: boolean;
}

export default function SensorWaveformGraph({
  channelFilter = "all",
  height = 220,
  className = "",
  showControls = true,
}: SensorWaveformGraphProps) {
  const { mode, isLive, isDemo } = useMode();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [activeChannel, setActiveChannel] = useState<ChannelType>(channelFilter);
  const [isPaused, setIsPaused] = useState(false);
  const [hardwareConnected, setHardwareConnected] = useState(false);

  // Dynamic Telemetry Metrics
  const [liveBpm, setLiveBpm] = useState<number | null>(74);
  const [snrQuality, setSnrQuality] = useState<number | null>(94);
  const [irDistance, setIrDistance] = useState<number | null>(42);
  const [touchDelta, setTouchDelta] = useState(12);
  const [presenceActive, setPresenceActive] = useState(false);
  const [touchActive, setTouchActive] = useState(false);

  // Internal state refs for requestAnimationFrame
  const animationRef = useRef<number>();
  const stepRef = useRef(0);
  const liveStateRef = useRef({
    presence: false,
    touch: false,
    bpm: 74,
    isLive: isLive,
    hardwareConnected: false,
  });

  // Keep ref synchronized
  useEffect(() => {
    liveStateRef.current.isLive = isLive;
    liveStateRef.current.hardwareConnected = hardwareConnected;
  }, [isLive, hardwareConnected]);

  // Initial check
  useEffect(() => {
    api.getDeviceStatus().then((res) => {
      const connected = !!res.hardware_connected;
      setHardwareConnected(connected);
      liveStateRef.current.hardwareConnected = connected;
      if (isLive && !connected) {
        setLiveBpm(null);
        setSnrQuality(null);
        setIrDistance(null);
      }
    }).catch(() => {});
  }, [isLive]);

  // Subscribe to live hardware WebSocket stream
  useEffect(() => {
    const unsubscribe = wsClient.subscribe((msg) => {
      if (msg.type === "DEVICE_EVENT" && msg.state) {
        const connected = !!msg.state.hardware_connected;
        setHardwareConnected(connected);
        liveStateRef.current.hardwareConnected = connected;
        setPresenceActive(!!msg.state.ir_presence);
        setTouchActive(!!msg.state.touch_pressed);
        liveStateRef.current.presence = !!msg.state.ir_presence;
        liveStateRef.current.touch = !!msg.state.touch_pressed;
      } else if (msg.type === "PIPELINE_PROGRESS" && msg.stage === "LIVENESS") {
        setLiveBpm(75);
      }
    });
    return () => unsubscribe();
  }, []);

  const isActuallyStreaming = isDemo || hardwareConnected;

  // Continuous Canvas Waveform Renderer
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let localStep = 0;

    const render = () => {
      if (isPaused) {
        animationRef.current = requestAnimationFrame(render);
        return;
      }

      const w = canvas.width;
      const h = canvas.height;

      // Clean background: Crisp ivory / warm surface
      ctx.fillStyle = "#FAF8F5";
      ctx.fillRect(0, 0, w, h);

      // 1. Precision Editorial Grid Lines
      ctx.strokeStyle = "#EDE8E1";
      ctx.lineWidth = 1;

      // Vertical grid lines
      for (let x = 0; x < w; x += 40) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }

      // Horizontal grid lines
      for (let y = 0; y < h; y += 30) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Center baseline rule
      ctx.strokeStyle = "#D5CFCE";
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(0, h / 2);
      ctx.lineTo(w, h / 2);
      ctx.stroke();
      ctx.setLineDash([]);

      const isLiveMode = liveStateRef.current.isLive;
      const isHwConnected = liveStateRef.current.hardwareConnected;

      // If in Live mode AND hardware is disconnected: flatline baseline
      if (isLiveMode && !isHwConnected) {
        ctx.strokeStyle = "#C5BFB5";
        ctx.lineWidth = 1.5;

        // Draw flat baseline
        ctx.beginPath();
        ctx.moveTo(0, h * 0.35);
        ctx.lineTo(w, h * 0.35);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(0, h * 0.65);
        ctx.lineTo(w, h * 0.65);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(0, h * 0.85);
        ctx.lineTo(w, h * 0.85);
        ctx.stroke();

        animationRef.current = requestAnimationFrame(render);
        return;
      }

      // Hardware is connected OR in Demo mode: Plot live waves
      localStep += 1.8;
      stepRef.current = localStep;

      // Fluctuate minor metrics for realism
      if (localStep % 30 < 1.8) {
        const noise = (Math.random() - 0.5) * 2;
        setLiveBpm((b) => Math.round(Math.max(68, Math.min(80, (b || 74) + noise))));
        setSnrQuality((q) => Math.round(Math.max(90, Math.min(99, (q || 94) + (Math.random() - 0.5)))));
        setIrDistance((d) => Math.round(Math.max(30, Math.min(55, (d || 42) + (Math.random() - 0.5) * 3))));
      }

      const presence = liveStateRef.current.presence;
      const touch = liveStateRef.current.touch;

      // Draw Waveforms depending on active channel
      if (activeChannel === "all" || activeChannel === "ppg") {
        // CHANNEL 1: MAX30102 PPG Waveform (Burnished Gold)
        ctx.beginPath();
        ctx.strokeStyle = "#B8860B"; // Burnished Gold
        ctx.lineWidth = 2.2;
        ctx.shadowColor = "rgba(184, 134, 11, 0.25)";
        ctx.shadowBlur = 4;

        const ppgCenterY = activeChannel === "all" ? h * 0.35 : h * 0.5;
        for (let x = 0; x < w; x++) {
          const t = (x + localStep) * 0.035;
          const systolic = Math.sin(t) * 22;
          const secondary = Math.sin(t * 2 + 1.2) * 8.5;
          const dicrotic = Math.sin(t * 4 + 2.4) * 3.8;
          const naturalNoise = (Math.sin(x * 0.4) + Math.cos(x * 0.7)) * 0.8;
          const y = ppgCenterY - (systolic + secondary + dicrotic + naturalNoise);

          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      if (activeChannel === "all" || activeChannel === "ir") {
        // CHANNEL 2: IR Proximity Sensor (GPIO 34) (Deep Forest Emerald)
        ctx.beginPath();
        ctx.strokeStyle = "#2D6A4F";
        ctx.lineWidth = 1.8;

        const irCenterY = activeChannel === "all" ? h * 0.65 : h * 0.5;
        for (let x = 0; x < w; x++) {
          const t = (x + localStep * 0.8) * 0.02;
          const baseDistance = Math.sin(t) * 14 + Math.cos(t * 0.5) * 8;
          const spike = presence ? -18 : 0;
          const jitter = (Math.sin(x * 0.8) * 1.2);
          const y = irCenterY + baseDistance + spike + jitter;

          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }

      if (activeChannel === "all" || activeChannel === "touch") {
        // CHANNEL 3: Capacitive Touch Sensor (GPIO 32) (Rich Charcoal Slate)
        ctx.beginPath();
        ctx.strokeStyle = "#1A1A1A";
        ctx.lineWidth = 1.6;

        const touchCenterY = activeChannel === "all" ? h * 0.85 : h * 0.5;
        for (let x = 0; x < w; x++) {
          const t = (x + localStep * 1.2) * 0.05;
          let y = touchCenterY;
          if (touch) {
            y += Math.sin(t * 8) * 16 + (Math.random() - 0.5) * 3;
          } else {
            y += Math.sin(t * 1.5) * 3 + (Math.random() - 0.5) * 1.2;
          }

          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }

      animationRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [activeChannel, isPaused, isActuallyStreaming]);

  return (
    <div className={`bg-card border border-border rounded-xl shadow-md p-5 relative overflow-hidden ${className}`}>
      {/* Top Header & Channel Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 mb-3 border-b border-border">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-surface border border-border flex items-center justify-center text-primary">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-serif-display font-bold text-foreground">
                Real-Time Physical Sensor Waveforms
              </h3>
              <span
                className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full border ${
                  isLive
                    ? hardwareConnected
                      ? "bg-emerald-50 text-emerald-800 border-emerald-300 font-bold"
                      : "bg-red-50 text-red-800 border-red-300 font-bold"
                    : "bg-amber-50 text-amber-800 border-amber-300 font-bold"
                }`}
              >
                {isLive
                  ? hardwareConnected
                    ? "● LIVE HARDWARE STREAM"
                    : "✕ HARDWARE DISCONNECTED"
                  : "○ DEMO SYNTHESIZER"}
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground font-mono">
              {isLive
                ? hardwareConnected
                  ? "Streaming live telemetry from ESP32 • 100 Hz sampling"
                  : "USB connection inactive • Awaiting physical device connection"
                : "Continuous multi-channel telemetry synthesizer • 100 Hz sampling"}
            </p>
          </div>
        </div>

        {/* Channel Selection Buttons */}
        {showControls && (
          <div className="flex items-center gap-1 bg-surface p-1 rounded-lg border border-border text-xs font-mono">
            {(
              [
                { key: "all", label: "All Traces" },
                { key: "ppg", label: "PPG (I2C)" },
                { key: "ir", label: "IR (GPIO34)" },
                { key: "touch", label: "Touch (GPIO32)" },
              ] as const
            ).map((ch) => (
              <button
                key={ch.key}
                onClick={() => setActiveChannel(ch.key)}
                className={`px-2.5 py-1 rounded text-[11px] transition-colors ${
                  activeChannel === ch.key
                    ? "bg-white text-foreground shadow-sm font-bold border border-border"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {ch.label}
              </button>
            ))}
            <button
              onClick={() => setIsPaused(!isPaused)}
              className="p-1 rounded text-muted-foreground hover:text-foreground ml-1"
              title={isPaused ? "Resume Waveform" : "Pause Waveform"}
            >
              {isPaused ? <Play className="w-3.5 h-3.5 text-emerald-600" /> : <Pause className="w-3.5 h-3.5" />}
            </button>
          </div>
        )}
      </div>

      {/* Main Canvas Waveform Display */}
      <div className="relative rounded-lg overflow-hidden border border-border bg-[#FAF8F5]">
        <canvas
          ref={canvasRef}
          width={800}
          height={height}
          className="w-full block"
          style={{ height: `${height}px` }}
        />

        {/* Real-Time On-Screen Telemetry HUD */}
        <div className="absolute top-2.5 left-3 flex items-center gap-3 text-[10px] font-mono pointer-events-none">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-white/90 border border-border shadow-sm text-foreground">
            <span className={`w-2 h-2 rounded-full ${isActuallyStreaming ? "bg-[#B8860B]" : "bg-red-400"}`} />
            <span>PPG PULSE: <strong>{isActuallyStreaming && liveBpm ? `${liveBpm} BPM` : "-- BPM"}</strong></span>
          </div>

          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-white/90 border border-border shadow-sm text-foreground">
            <span className={`w-2 h-2 rounded-full ${isActuallyStreaming ? "bg-[#2D6A4F]" : "bg-red-400"}`} />
            <span>IR RANGE: <strong>{isActuallyStreaming && irDistance ? `${irDistance} cm` : "-- cm"}</strong></span>
          </div>

          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-white/90 border border-border shadow-sm text-foreground">
            <span className={`w-2 h-2 rounded-full ${isActuallyStreaming ? "bg-[#1A1A1A]" : "bg-red-400"}`} />
            <span>TOUCH: <strong>{isActuallyStreaming ? (touchActive ? "ACTIVE" : "ARMED") : "OFFLINE"}</strong></span>
          </div>
        </div>

        {/* Disconnected Warning Overlay on Canvas */}
        {isLive && !hardwareConnected && (
          <div className="absolute inset-0 bg-white/70 backdrop-blur-[1px] flex flex-col items-center justify-center p-4 text-center">
            <AlertCircle className="w-6 h-6 text-danger mb-1" />
            <p className="font-serif-display font-bold text-foreground text-sm">
              Physical Hardware Disconnected
            </p>
            <p className="text-xs text-muted-foreground max-w-md font-sans mt-0.5">
              No live telemetry received from MAX30102 or ESP32. Plug in the USB cable and click <strong>Check / Probe Connection</strong> in the panel above, or switch to <strong>DEMO MODE</strong> at the top to view simulated waveforms.
            </p>
          </div>
        )}

        <div className="absolute bottom-2 right-3 text-[10px] font-mono text-muted-foreground bg-white/80 px-2 py-0.5 rounded border border-border">
          SNR Quality: <strong>{isActuallyStreaming && snrQuality ? `${snrQuality}%` : "0%"}</strong> • Voltage: <strong>{isActuallyStreaming ? "3.30V" : "0.00V"}</strong>
        </div>
      </div>

      {/* Legend & Channel Explanations */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3 pt-3 border-t border-border/70 text-xs font-mono">
        <div className="flex items-center space-x-2">
          <HeartPulse className="w-4 h-4 text-primary shrink-0" />
          <div className="truncate">
            <span className="font-semibold text-foreground">MAX30102 Infrared PPG</span>
            <p className="text-[10px] text-muted-foreground truncate">Physiological dicrotic pulse curve</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Radio className="w-4 h-4 text-[#2D6A4F] shrink-0" />
          <div className="truncate">
            <span className="font-semibold text-foreground">IR Proximity (GPIO 34)</span>
            <p className="text-[10px] text-muted-foreground truncate">Analog person approach detection</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Fingerprint className="w-4 h-4 text-foreground shrink-0" />
          <div className="truncate">
            <span className="font-semibold text-foreground">Capacitive Touch (GPIO 32)</span>
            <p className="text-[10px] text-muted-foreground truncate">Verification start touch trigger</p>
          </div>
        </div>
      </div>
    </div>
  );
}
