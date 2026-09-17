"use client";

import { useEffect, useState } from "react";
import { Sparkles, Play, CheckCircle2, AlertTriangle, XCircle, Lock, Unlock } from "lucide-react";
import AiTracePanel from "@/components/AiTracePanel";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/ws";
import { useMode } from "@/context/ModeContext";

export default function DemoControlCenter() {
  const { mode, isLive, isDemo, setMode } = useMode();
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>("A");
  const [actuateHardware, setActuateHardware] = useState<boolean>(true);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  // Trace results
  const [agentResults, setAgentResults] = useState<any[]>([]);
  const [finalDecision, setFinalDecision] = useState<"PASS" | "REVIEW" | "FAIL" | null>(null);
  const [finalConfidence, setFinalConfidence] = useState(0.0);
  const [finalReasons, setFinalReasons] = useState<string[]>([]);
  const [gateAction, setGateAction] = useState<string>("KEEP_LOCKED");

  useEffect(() => {
    api.getDemoScenarios().then(setScenarios).catch(console.error);

    const unsubscribe = wsClient.subscribe((msg) => {
      if (msg.type === "PIPELINE_PROGRESS" && msg.details?.result) {
        setAgentResults((prev) => {
          const filtered = prev.filter((r) => r.agent !== msg.details.result.agent);
          return [...filtered, msg.details.result];
        });
      } else if (msg.type === "DEMO_SCENARIO_COMPLETE") {
        setFinalDecision(msg.decision);
        setFinalConfidence(msg.confidence);
        setFinalReasons(msg.reasons || []);
        setGateAction(msg.gate_action);
        setIsRunning(false);
      }
    });

    return () => unsubscribe();
  }, []);

  const handleRun = async (key: string) => {
    setIsRunning(true);
    setSelectedScenario(key);
    setAgentResults([]);
    setFinalDecision(null);

    try {
      const res = await api.runDemoScenario(key, actuateHardware);
      setFinalDecision(res.decision);
      setFinalConfidence(res.confidence);
      setFinalReasons(res.reasons);
      setAgentResults(res.agent_results);
      setGateAction(res.gate_action);
    } catch (err: any) {
      console.error("Demo run error:", err);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Editorial Masthead Banner */}
      <div className="bg-card border border-border rounded-xl p-6 sm:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1.5 max-w-2xl">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded font-mono text-[10px] font-bold uppercase bg-amber-50 text-amber-900 border border-amber-300">
              DEMONSTRATION REPERTOIRE
            </span>
            <span className="text-xs font-mono text-muted-foreground">
              Deterministic Test Pathways
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif-display font-black text-foreground tracking-tight">
            Trust Gate Demonstration Suite
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground font-sans leading-relaxed">
            Execute all 6 PRD verification scenarios with deterministic multi-agent inputs, real-time evidence aggregation, and physical ESP32 servo turnstile actuation.
          </p>
        </div>

        {/* Servo Actuation Checkbox */}
        <div className="flex items-center space-x-3 bg-surface border border-border p-3.5 rounded-lg font-mono text-xs text-foreground shrink-0 shadow-inner">
          <input
            type="checkbox"
            id="servoActuate"
            checked={actuateHardware}
            onChange={(e) => setActuateHardware(e.target.checked)}
            className="w-4 h-4 accent-primary rounded cursor-pointer"
          />
          <label htmlFor="servoActuate" className="cursor-pointer font-medium select-none">
            Actuate Physical ESP32 Servo
          </label>
        </div>
      </div>

      {/* Main Grid: Scenario Selector vs Trace Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Scenarios Grid */}
        <div className="lg:col-span-6 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-border">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-muted-foreground small-caps">
              Select Verification Scenario (A–F)
            </h2>
            <span className="text-[10px] font-mono text-muted-foreground">6 Scenarios Available</span>
          </div>

          <div className="grid grid-cols-1 gap-3.5">
            {scenarios.map((sc) => {
              const isSelected = selectedScenario === sc.key;
              const isPass = sc.expected_decision === "PASS";
              const isReview = sc.expected_decision === "REVIEW";

              return (
                <div
                  key={sc.key}
                  onClick={() => !isRunning && setSelectedScenario(sc.key)}
                  className={`p-4 rounded-xl border text-left cursor-pointer transition-all ${
                    isSelected
                      ? "bg-card border-primary shadow-sm ring-1 ring-primary/40"
                      : "bg-surface/50 border-border hover:border-border-hover hover:bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-serif-display font-bold text-foreground">
                      Scenario {sc.key}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                        isPass
                          ? "bg-success-surface text-success border-success/30"
                          : isReview
                          ? "bg-warning-surface text-warning border-warning/30"
                          : "bg-danger-surface text-danger border-danger/30"
                      }`}
                    >
                      Expected: {sc.expected_decision} (Gate: {sc.gate_action})
                    </span>
                  </div>

                  <h3 className="text-sm font-serif-display font-bold text-foreground">{sc.title}</h3>
                  <p className="text-xs text-muted-foreground font-sans mt-1 leading-relaxed">
                    {sc.description}
                  </p>

                  <div className="mt-3.5 flex items-center justify-between pt-2.5 border-t border-border/60">
                    <span className="text-[10px] font-mono text-muted-foreground">
                      Risk: {sc.risk_level} • Confidence: ~{Math.round(sc.expected_confidence * 100)}%
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRun(sc.key);
                      }}
                      disabled={isRunning}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-primary hover:bg-primary-hover text-white font-serif-display font-bold text-xs shadow-sm transition-all active:scale-95"
                    >
                      <Play className="w-3.5 h-3.5" />
                      {isRunning && isSelected ? "Executing..." : "Execute Scenario"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Real-time Live Trace Panel */}
        <div className="lg:col-span-6 space-y-5">
          <AiTracePanel
            agentResults={agentResults}
            finalDecision={finalDecision}
            finalConfidence={finalConfidence}
            finalReasons={finalReasons}
            isDemo={true}
          />

          {/* Physical Servo Reaction Card */}
          {finalDecision && (
            <div
              className={`p-5 rounded-xl border text-center font-mono transition-all ${
                gateAction === "OPEN_GATE"
                  ? "bg-success-surface border-success/40 text-success"
                  : "bg-surface border-border text-foreground"
              }`}
            >
              <div className="flex items-center justify-center mb-1">
                {gateAction === "OPEN_GATE" ? (
                  <Unlock className="w-6 h-6 text-success animate-bounce" />
                ) : (
                  <Lock className="w-6 h-6 text-muted-foreground" />
                )}
              </div>
              <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">
                ESP32 Hardware Physical Reaction
              </p>
              <h4 className="text-lg font-serif-display font-bold mt-1 text-foreground">
                {gateAction === "OPEN_GATE" ? "SERVO ACTUATED: GATE OPEN (90°)" : "SERVO REMAINS LOCKED (0°)"}
              </h4>
              <p className="text-xs text-muted-foreground font-sans mt-1">
                {gateAction === "OPEN_GATE"
                  ? "Authoritative OPEN_GATE dispatched to hardware controller. Auto-locks in 5 seconds."
                  : "Physical barrier secured. Requires manual desk resolution."}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
