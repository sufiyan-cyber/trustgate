"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  TrendingUp,
  ScanFace,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Cpu,
  Layers,
} from "lucide-react";
import HardwareStatusGrid from "@/components/HardwareStatusGrid";
import SensorWaveformGraph from "@/components/SensorWaveformGraph";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/ws";
import { useMode } from "@/context/ModeContext";

export default function DashboardPage() {
  const { mode, isLive, isDemo, setMode } = useMode();
  const [stats, setStats] = useState<any>(null);
  const [recentSessions, setRecentSessions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadData = async () => {
    try {
      const data = await api.getDashboardStats();
      setStats(data.metrics);
      setRecentSessions(data.recent_sessions || []);
    } catch (err) {
      console.error("Failed to load dashboard metrics:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Listen for real-time verification updates from FastAPI backend
    const unsubscribe = wsClient.subscribe((msg) => {
      if (
        msg.type === "VERIFICATION_COMPLETE" ||
        msg.type === "SESSION_STARTED" ||
        msg.type === "ADMIN_REVIEW_ACTION"
      ) {
        loadData();
      }
    });

    return () => unsubscribe();
  }, []);

  const statCards = [
    {
      roman: "I",
      label: "Total Verifications",
      value: stats?.total_verifications ?? 0,
      icon: TrendingUp,
      accent: "text-foreground",
      border: "border-border",
    },
    {
      roman: "II",
      label: "Access Authorized (Pass)",
      value: stats?.passed_count ?? 0,
      icon: CheckCircle2,
      accent: "text-success",
      border: "border-success/30",
    },
    {
      roman: "III",
      label: "Flagged for Desk Review",
      value: stats?.review_count ?? 0,
      icon: AlertTriangle,
      accent: "text-warning",
      border: "border-warning/30",
    },
    {
      roman: "IV",
      label: "Verification Rejected",
      value: stats?.failed_count ?? 0,
      icon: XCircle,
      accent: "text-danger",
      border: "border-danger/30",
    },
  ];

  // Filter recent sessions if user wants to isolate live vs demo, or show all
  const filteredSessions = recentSessions.filter((s) => {
    if (isLive) return !s.is_demo;
    return true; // in demo mode show all or demo
  });

  return (
    <div className="space-y-8">
      {/* Editorial Masthead Header */}
      <div className="bg-card border border-border rounded-xl p-6 sm:p-8 shadow-sm relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-1.5 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary" />
              <span className="text-xs font-mono font-semibold uppercase tracking-widest text-primary small-caps">
                Command Dispatch • Node TG-001
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-serif-display font-black tracking-tight text-foreground">
              Trust Gate Identity & Access Dispatch
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground font-sans leading-relaxed">
              Deterministic multi-agent verification gateway integrating physical ESP32 peripherals, AWS Textract document extraction, deep facial embeddings, and turnstile servo actuation.
            </p>
          </div>

          {/* Quick Action Navigation Buttons */}
          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <button
              onClick={loadData}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-md bg-surface border border-border text-xs font-mono text-foreground hover:bg-surface/70 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Sync Ledger
            </button>

            <Link
              href="/verify"
              className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary hover:bg-primary-hover text-white font-serif-display font-bold text-xs shadow-sm transition-all active:scale-95"
            >
              <ScanFace className="w-4 h-4" />
              Launch Kiosk
            </Link>

            <Link
              href="/demo"
              className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-white hover:bg-surface text-foreground border border-border text-xs font-mono font-medium transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              Demo Scenarios (A–F)
            </Link>

            <Link
              href="/simulator"
              className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-surface border border-border text-xs font-mono text-muted-foreground hover:text-foreground transition-colors"
            >
              <Cpu className="w-3.5 h-3.5 text-primary" />
              Simulator
            </Link>
          </div>
        </div>

        {/* Mode Indicator Banner */}
        <div className="mt-5 pt-4 border-t border-border flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs font-mono gap-2 text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-foreground">CURRENT OPERATING MODE:</span>
            <span
              className={`px-2.5 py-0.5 rounded font-bold uppercase ${
                isLive
                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  : "bg-amber-50 text-amber-800 border border-amber-200"
              }`}
            >
              {isLive ? "● LIVE GATEWAY (Physical Sensors & Camera)" : "○ DEMO MODE (Mock Scenarios & Fallbacks)"}
            </span>
          </div>
          <div>
            {isLive ? (
              <span>Streaming authentic physical GPIO and camera telemetry</span>
            ) : (
              <span>Simulated verification data and fallback manual approvals enabled</span>
            )}
          </div>
        </div>
      </div>

      {/* Real-Time Continuous Sensor Waveform Graph */}
      <SensorWaveformGraph height={220} />

      {/* Live Hardware Telemetry Grid */}
      <HardwareStatusGrid />

      {/* High-Level Metric Stat Cards (Roman I to IV) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`p-5 rounded-xl border ${card.border} bg-card shadow-sm flex items-center justify-between`}
            >
              <div>
                <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                  <span className="font-serif-display font-bold text-xs">{card.roman}.</span>
                  <p className="text-[11px] font-mono uppercase tracking-wider small-caps font-semibold">
                    {card.label}
                  </p>
                </div>
                <p className={`text-3xl font-serif-display font-black tracking-tight ${card.accent}`}>
                  {card.value}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-surface border border-border text-foreground">
                <Icon className="w-5 h-5" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Verification Sessions Ledger */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-5 pb-3 border-b border-border">
          <div>
            <h2 className="text-base font-serif-display font-bold text-foreground">
              Verification Audit Ledger
            </h2>
            <p className="text-xs text-muted-foreground font-mono">
              Immutable physical access transaction log • {filteredSessions.length} sessions displayed
            </p>
          </div>
          <Link
            href="/review"
            className="text-xs font-mono text-primary hover:underline flex items-center gap-1 font-semibold"
          >
            Open Admin Review Queue <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-border text-muted-foreground">
                <th className="pb-3 font-semibold">Session ID</th>
                <th className="pb-3 font-semibold">Participant</th>
                <th className="pb-3 font-semibold">Device</th>
                <th className="pb-3 font-semibold">Verdict</th>
                <th className="pb-3 font-semibold">Confidence</th>
                <th className="pb-3 font-semibold">Risk Level</th>
                <th className="pb-3 font-semibold">Timestamp</th>
                <th className="pb-3 font-semibold text-right">Mode</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60 text-foreground">
              {filteredSessions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-muted-foreground font-sans">
                    {isLive
                      ? "No live verification sessions recorded yet. Approach the camera or press the touch sensor to initiate a scan."
                      : "No demonstration sessions recorded yet. Switch to Demo Mode or execute Scenario A."}
                  </td>
                </tr>
              ) : (
                filteredSessions.map((session) => (
                  <tr key={session.id} className="hover:bg-surface/50 transition-colors">
                    <td className="py-3.5 font-bold text-foreground">#{session.id.slice(0, 8)}</td>
                    <td className="py-3.5 font-sans font-medium text-foreground">
                      {session.participant_name}
                    </td>
                    <td className="py-3.5 text-muted-foreground">{session.device_id}</td>
                    <td className="py-3.5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold border ${
                          session.decision === "PASS"
                            ? "bg-success-surface text-success border-success/30"
                            : session.decision === "REVIEW"
                            ? "bg-warning-surface text-warning border-warning/30"
                            : "bg-danger-surface text-danger border-danger/30"
                        }`}
                      >
                        {session.decision}
                      </span>
                    </td>
                    <td className="py-3.5 font-semibold text-foreground">
                      {Math.round((session.confidence || 0) * 100)}%
                    </td>
                    <td className="py-3.5">
                      <span
                        className={`text-[10px] uppercase font-bold ${
                          session.risk_level === "LOW"
                            ? "text-success"
                            : session.risk_level === "HIGH"
                            ? "text-danger"
                            : "text-warning"
                        }`}
                      >
                        {session.risk_level}
                      </span>
                    </td>
                    <td className="py-3.5 text-muted-foreground">
                      {session.started_at ? new Date(session.started_at).toLocaleTimeString() : "—"}
                    </td>
                    <td className="py-3.5 text-right">
                      {session.is_demo ? (
                        <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                          Demo
                        </span>
                      ) : (
                        <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                          Live
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
