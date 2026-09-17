"use client";

import { useEffect, useRef, useState } from "react";
import { HeartPulse, Activity } from "lucide-react";

interface LivenessVisualizerProps {
  onComplete?: (data: {
    pulse_detected: boolean;
    signal_quality: number;
    bpm: number;
    duration_ms: number;
  }) => void;
  isActive?: boolean;
}

export default function LivenessVisualizer({
  onComplete,
  isActive = false,
}: LivenessVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [bpm, setBpm] = useState(74);
  const [quality, setQuality] = useState(0.93);
  const [progress, setProgress] = useState(0);
  const [fingerDetected, setFingerDetected] = useState(false);

  useEffect(() => {
    if (!isActive) {
      setProgress(0);
      setFingerDetected(false);
      return;
    }

    setFingerDetected(true);
    let currentProgress = 0;
    const interval = setInterval(() => {
      currentProgress += 2.5; // reaches 100 in 4 seconds
      setProgress(Math.min(100, Math.round(currentProgress)));

      // Subtle natural heart-rate fluctuation
      setBpm(Math.round(72 + Math.sin(currentProgress / 10) * 4));

      if (currentProgress >= 100) {
        clearInterval(interval);
        if (onComplete) {
          onComplete({
            pulse_detected: true,
            signal_quality: 0.94,
            bpm: 74,
            duration_ms: 4000,
          });
        }
      }
    }, 100);

    return () => clearInterval(interval);
  }, [isActive, onComplete]);

  // PPG Pulse Waveform Rendering on Precision Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrame: number;
    let step = 0;

    const render = () => {
      const w = canvas.width;
      const h = canvas.height;

      // Ivory/cream canvas background
      ctx.fillStyle = "#FAF8F5";
      ctx.fillRect(0, 0, w, h);

      // Fine editorial grid lines
      ctx.strokeStyle = "#EDE8E1";
      ctx.lineWidth = 1;
      for (let x = 0; x < w; x += 25) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Draw PPG Waveform
      ctx.strokeStyle = fingerDetected ? "#B8860B" : "#A39E93";
      ctx.lineWidth = 2.2;
      ctx.beginPath();

      const centerY = h / 2;
      for (let x = 0; x < w; x++) {
        const t = (x + step) * 0.045;
        // Synthesized dicrotic notch PPG curve
        let y = centerY;
        if (fingerDetected) {
          const fundamental = Math.sin(t) * 24;
          const harmonic = Math.sin(t * 2 + 1.2) * 9.5;
          const dicrotic = Math.sin(t * 4 + 2.5) * 4.2;
          y = centerY - (fundamental + harmonic + dicrotic);
        } else {
          y = centerY + (Math.random() - 0.5) * 4;
        }

        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      step += 2.5;
      animationFrame = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationFrame);
  }, [fingerDetected]);

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-border">
        <div className="flex items-center space-x-2">
          <HeartPulse className="w-5 h-5 text-primary animate-pulse" />
          <h4 className="text-sm font-serif-display font-bold text-foreground">
            MAX30102 Photoplethysmogram (PPG)
          </h4>
        </div>
        <div className="flex items-center space-x-3 text-xs font-mono">
          <span className="text-muted-foreground">
            {fingerDetected ? "CONTACT DETECTED" : "AWAITING SENSOR TOUCH"}
          </span>
          <span className="px-2.5 py-0.5 rounded bg-surface text-foreground font-bold border border-border">
            {bpm} BPM
          </span>
        </div>
      </div>

      {/* Canvas for Waveform */}
      <div className="relative rounded-lg overflow-hidden border border-border bg-[#FAF8F5]">
        <canvas ref={canvasRef} width={600} height={120} className="w-full h-28 block" />
        <div className="absolute bottom-2 left-3 text-[10px] font-mono text-muted-foreground flex items-center gap-1.5">
          <Activity className="w-3 h-3 text-primary" />
          Infrared Channel Signal • 100 Hz Sampling
        </div>
      </div>

      {/* Progress & Quality */}
      <div className="mt-4 space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-muted-foreground">
          <span>Acquisition: {Math.round((progress / 100) * 4)}s / 4.0s</span>
          <span>SNR Quality: {Math.round(quality * 100)}%</span>
        </div>
        <div className="w-full h-2 bg-surface rounded-full overflow-hidden border border-border">
          <div
            className="h-full bg-primary transition-all duration-150"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-[11px] text-muted-foreground text-center italic font-serif">
          Maintain steady fingertip pressure on sensor optical window until capture completes.
        </p>
      </div>
    </div>
  );
}
