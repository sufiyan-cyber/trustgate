"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShieldCheck,
  LayoutDashboard,
  ScanFace,
  ClipboardCheck,
  Sparkles,
  Cpu,
  RefreshCw,
} from "lucide-react";
import { useEffect, useState } from "react";
import { wsClient } from "@/lib/ws";
import { useMode } from "@/context/ModeContext";
import { api } from "@/lib/api";

export default function Navbar() {
  const pathname = usePathname();
  const { mode, isLive, isDemo, setMode } = useMode();
  const [hardwareConnected, setHardwareConnected] = useState(false);
  const [connectedPort, setConnectedPort] = useState<string | null>(null);
  const [flaggedCount, setFlaggedCount] = useState(0);
  const [isProbing, setIsProbing] = useState(false);

  const checkStatus = () => {
    api.getDeviceStatus().then((res) => {
      setHardwareConnected(!!res.hardware_connected);
      setConnectedPort(res.connected_port || null);
    }).catch(() => {});
  };

  useEffect(() => {
    checkStatus();

    api.getFlaggedReviews().then((reviews) => {
      setFlaggedCount(reviews.length || 0);
    }).catch(() => {});

    const unsubscribe = wsClient.subscribe((msg) => {
      if (msg.type === "DEVICE_EVENT") {
        if (msg.state) {
          setHardwareConnected(!!msg.state.hardware_connected);
          setConnectedPort(msg.state.connected_port || null);
        }
      } else if (msg.type === "VERIFICATION_COMPLETE" || msg.type === "ADMIN_REVIEW_ACTION") {
        api.getFlaggedReviews().then((reviews) => {
          setFlaggedCount(reviews.length || 0);
        }).catch(() => {});
      }
    });
    return () => unsubscribe();
  }, []);

  const handleProbe = async () => {
    setIsProbing(true);
    try {
      const res = await api.probeDevice("TG-001");
      setHardwareConnected(!!res.hardware_connected);
      setConnectedPort(res.connected_port || null);
      if (!res.hardware_connected) {
        alert(res.message || "No physical ESP32 detected on USB ports.");
      }
    } catch (e: any) {
      alert("Failed to probe hardware: " + e.message);
    } finally {
      setIsProbing(false);
    }
  };

  const navItems = [
    { label: "Dashboard", href: "/", icon: LayoutDashboard },
    { label: "Verification Kiosk", href: "/verify", icon: ScanFace },
    {
      label: "Admin Review",
      href: "/review",
      icon: ClipboardCheck,
      badge: flaggedCount > 0 ? flaggedCount : undefined,
    },
    { label: "Demo Scenarios", href: "/demo", icon: Sparkles },
    { label: "Hardware Simulator", href: "/simulator", icon: Cpu },
  ];

  return (
    <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-md border-b border-border shadow-sm">
      {/* Top Thin Masthead Rule */}
      <div className="h-[2px] bg-gradient-to-r from-transparent via-primary/60 to-transparent w-full" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-18 py-2">
          {/* Brand Masthead */}
          <Link href="/" className="flex items-center space-x-3.5 group">
            <div className="w-10 h-10 rounded-lg bg-surface border border-border flex items-center justify-center text-primary group-hover:border-primary/60 transition-all shadow-sm">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-serif-display text-xl font-bold tracking-tight text-foreground">
                  TRUST GATE
                </span>
                <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-surface text-primary border border-border">
                  Vol. 1
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground font-mono tracking-wide">
                Physical Identity & Biometric Gateway
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`relative flex items-center space-x-2 px-3.5 py-2 rounded-md text-xs font-semibold small-caps tracking-wider transition-all ${
                    isActive
                      ? "bg-white text-foreground shadow-sm border border-border"
                      : "text-muted-foreground hover:text-foreground hover:bg-surface"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-primary" : "text-muted-foreground"}`} />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-danger text-white">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Right Actions: Top Live / Demo Switch & Device Status */}
          <div className="flex items-center space-x-3">
            {/* Mode Switch Pill Toggle */}
            <div className="flex items-center p-1 rounded-full bg-surface border border-border shadow-inner text-xs font-mono">
              <button
                type="button"
                onClick={() => setMode("LIVE")}
                className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-[11px] font-semibold transition-all ${
                  isLive
                    ? "bg-emerald-700 text-white shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                title="Switch to Live Mode (Authentic Hardware Telemetry Only)"
              >
                <span className={`w-2 h-2 rounded-full ${isLive ? (hardwareConnected ? "bg-emerald-300 animate-pulse" : "bg-red-400") : "bg-muted-foreground/40"}`} />
                <span>LIVE</span>
              </button>

              <button
                type="button"
                onClick={() => setMode("DEMO")}
                className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-[11px] font-semibold transition-all ${
                  isDemo
                    ? "bg-primary text-white shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                title="Switch to Demo Mode (Mock Cases & Waveform Synthesizer)"
              >
                <span className={`w-2 h-2 rounded-full ${isDemo ? "bg-amber-200 animate-pulse" : "bg-muted-foreground/40"}`} />
                <span>DEMO</span>
              </button>
            </div>

            {/* ESP32 Hardware Status Badge */}
            <div className="hidden sm:flex items-center space-x-2 bg-white px-3 py-1.5 rounded-md border border-border shadow-sm">
              {isLive ? (
                <>
                  <span
                    className={`w-2 h-2 rounded-full ${
                      hardwareConnected
                        ? "bg-emerald-600 shadow-[0_0_6px_rgba(16,185,129,0.5)]"
                        : "bg-red-500"
                    }`}
                  />
                  <span className="text-[11px] font-mono text-foreground font-medium">
                    {hardwareConnected
                      ? `ESP32: ${connectedPort || "CONNECTED"}`
                      : "ESP32: NOT CONNECTED (USB)"}
                  </span>
                  <button
                    onClick={handleProbe}
                    disabled={isProbing}
                    className="ml-1 px-1.5 py-0.5 rounded bg-surface hover:bg-surface/80 border border-border text-[10px] font-mono text-muted-foreground hover:text-foreground transition-colors"
                    title="Check USB ports and verify ESP32 connection"
                  >
                    {isProbing ? <RefreshCw className="w-3 h-3 animate-spin" /> : "Check"}
                  </button>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  <span className="text-[11px] font-mono text-foreground font-medium">
                    ESP32: DEMO EMULATOR
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
