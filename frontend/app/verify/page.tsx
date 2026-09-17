"use client";

import { useEffect, useState } from "react";
import {
  ScanFace,
  CreditCard,
  HeartPulse,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Unlock,
  Lock,
  RefreshCw,
  Fingerprint,
  Zap,
  Volume2,
  VolumeX,
  Info,
} from "lucide-react";
import VerificationProgress from "@/components/VerificationProgress";
import CameraCapture from "@/components/CameraCapture";
import LivenessVisualizer from "@/components/LivenessVisualizer";
import AiTracePanel from "@/components/AiTracePanel";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/ws";
import { useMode } from "@/context/ModeContext";

export default function VerificationKioskPage() {
  const { mode, isLive, isDemo } = useMode();
  const [currentStage, setCurrentStage] = useState(1);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);

  // Verification Assets
  const [idBlob, setIdBlob] = useState<Blob | null>(null);
  const [selfieBlob, setSelfieBlob] = useState<Blob | null>(null);
  const [livenessResult, setLivenessResult] = useState<any>(null);

  // Result & AI Trace State
  const [agentResults, setAgentResults] = useState<any[]>([]);
  const [finalDecision, setFinalDecision] = useState<"PASS" | "REVIEW" | "FAIL" | null>(null);
  const [finalConfidence, setFinalConfidence] = useState(0.0);
  const [finalReasons, setFinalReasons] = useState<string[]>([]);
  const [gateCommand, setGateCommand] = useState<string>("KEEP_LOCKED");

  const speakInstruction = (text: string) => {
    if (typeof window !== "undefined" && "speechSynthesis" in window && voiceEnabled) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  };

  // Subscribe to real-time agent updates
  useEffect(() => {
    const unsubscribe = wsClient.subscribe((msg) => {
      if (msg.type === "PIPELINE_PROGRESS" && msg.details?.result) {
        setAgentResults((prev) => {
          const filtered = prev.filter((r) => r.agent !== msg.details.result.agent);
          return [...filtered, msg.details.result];
        });
      } else if (msg.type === "VERIFICATION_COMPLETE") {
        setFinalDecision(msg.decision);
        setFinalConfidence(msg.confidence);
        setFinalReasons(msg.reasons || []);
        setGateCommand(msg.gate_command);
        setCurrentStage(8);
        setIsEvaluating(false);
        if (msg.decision === "PASS") {
          speakInstruction("Verification approved. Access granted. Please proceed through the turnstile.");
        } else {
          speakInstruction("Verification flagged. Please proceed to the registration desk.");
        }
      }
    });

    return () => unsubscribe();
  }, [voiceEnabled]);

  // Trigger voice cues when stage changes
  useEffect(() => {
    if (currentStage === 1) {
      speakInstruction("Please hold your ID card up to the camera inside the frame.");
    } else if (currentStage === 2) {
      speakInstruction("Now look directly into the camera lens to capture your face.");
    } else if (currentStage === 5) {
      speakInstruction("Please rest your finger steadily upon the pulse sensor.");
    }
  }, [currentStage, voiceEnabled]);

  // Auto-start session on initial kiosk load so camera prompts immediately
  useEffect(() => {
    if (!sessionId && !isInitializing) {
      handleStartSession();
    }
  }, [isDemo]);

  // 1. Start Session
  const handleStartSession = async () => {
    setIsInitializing(true);
    try {
      const res = await api.startVerification("TG-001", isDemo);
      setSessionId(res.session_id);
      setCurrentStage(1);
      setAgentResults([]);
      setFinalDecision(null);
      setIdBlob(null);
      setSelfieBlob(null);
      setLivenessResult(null);
      setGateCommand("KEEP_LOCKED");
    } catch (err) {
      console.error("Failed to start session:", err);
    } finally {
      setIsInitializing(false);
    }
  };

  // Demo Fast-Track Preload (for demo fallback)
  const handleDemoPreset = async (type: "pass" | "review" | "fail") => {
    setIsInitializing(true);
    try {
      const res = await api.startVerification("TG-001", true);
      setSessionId(res.session_id);

      const canvas = document.createElement("canvas");
      canvas.width = 400;
      canvas.height = 250;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.fillStyle = "#EAE6DF";
        ctx.fillRect(0, 0, 400, 250);
        ctx.fillStyle = "#1A1A1A";
        ctx.font = "bold 16px sans-serif";
        ctx.fillText(type === "pass" ? "AARAV SHARMA" : type === "review" ? "PRIYA PATEL" : "UNREGISTERED", 20, 50);
        ctx.font = "12px monospace";
        ctx.fillText(type === "pass" ? "ID: DEL-2026-89412" : "ID: MUM-2026-11045", 20, 80);
      }

      canvas.toBlob(async (blob) => {
        if (blob) {
          await api.uploadDocument(res.session_id, blob);
          await api.uploadSelfie(res.session_id, blob);
          await api.submitLiveness(res.session_id, {
            pulse_detected: true,
            signal_quality: 0.94,
            bpm: 74,
            duration_ms: 4000,
          });
          setCurrentStage(7);
          setIsEvaluating(true);
          const evalRes = await api.runVerification(res.session_id);
          setFinalDecision(evalRes.decision);
          setFinalConfidence(evalRes.confidence);
          setFinalReasons(evalRes.reasons);
          setAgentResults(evalRes.agent_results);
          setGateCommand(evalRes.gate_command);
          setCurrentStage(8);
          setIsEvaluating(false);
        }
      });
    } catch (err) {
      console.error("Demo preset error:", err);
    } finally {
      setIsInitializing(false);
    }
  };

  // 2. Handle ID Captured
  const handleIdCaptured = async (blob: Blob) => {
    setIdBlob(blob);
    if (!sessionId) {
      const res = await api.startVerification("TG-001", isDemo);
      setSessionId(res.session_id);
      await api.uploadDocument(res.session_id, blob);
    } else {
      await api.uploadDocument(sessionId, blob);
    }
    setCurrentStage(2);
  };

  // 3. Handle Selfie Captured
  const handleSelfieCaptured = async (blob: Blob) => {
    setSelfieBlob(blob);
    if (sessionId) {
      await api.uploadSelfie(sessionId, blob);
    }
    setCurrentStage(5); // Proceed to Liveness
  };

  // 4. Handle Liveness Complete
  const handleLivenessDone = async (data: any) => {
    setLivenessResult(data);
    if (sessionId) {
      await api.submitLiveness(sessionId, data);
    }
    setCurrentStage(7); // Ready to run AI pipeline
  };

  // 5. Trigger Multi-Agent Pipeline
  const handleRunPipeline = async () => {
    if (!sessionId) return;
    setIsEvaluating(true);
    setCurrentStage(7);

    try {
      const res = await api.runVerification(sessionId);
      setFinalDecision(res.decision);
      setFinalConfidence(res.confidence);
      setFinalReasons(res.reasons);
      setAgentResults(res.agent_results);
      setGateCommand(res.gate_command);
      setCurrentStage(8);
    } catch (err) {
      console.error("Pipeline run error:", err);
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded border ${
                isLive
                  ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                  : "bg-amber-50 text-amber-800 border-amber-300"
              }`}
            >
              {isLive ? "● LIVE HARDWARE STATION" : "○ DEMO MODE ACTIVE"}
            </span>
          </div>
          <h1 className="text-2xl font-serif-display font-black text-foreground tracking-tight flex items-center gap-2.5">
            <ScanFace className="w-6 h-6 text-primary" />
            Verification Kiosk
          </h1>
          <p className="text-xs text-muted-foreground font-mono">
            {sessionId ? `Active Session: #${sessionId.slice(0, 12)}` : "Initializing camera and sensors..."}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Voice Guidance Toggle */}
          <button
            onClick={() => {
              setVoiceEnabled(!voiceEnabled);
              if (!voiceEnabled) speakInstruction("Voice guidance activated.");
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-xs font-mono transition-colors ${
              voiceEnabled
                ? "bg-primary text-white border-primary"
                : "bg-surface text-muted-foreground border-border hover:text-foreground"
            }`}
            title="Toggle Voice Guidance"
          >
            {voiceEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
            <span>Voice: {voiceEnabled ? "ON" : "OFF"}</span>
          </button>

          <button
            onClick={handleStartSession}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-surface border border-border text-xs font-mono text-foreground hover:bg-surface/70 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset & New Session
          </button>
        </div>
      </div>

      {/* Demo Quick-Fill Bar (Only Visible in Demo Mode) */}
      {isDemo && (
        <div className="p-3 rounded-lg bg-amber-50/70 border border-amber-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2 text-amber-900 font-medium">
            <Zap className="w-4 h-4 text-primary shrink-0" />
            <span>Demo Mode Presets: Quick-test complete pipeline execution</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleDemoPreset("pass")}
              disabled={isInitializing}
              className="px-2.5 py-1 rounded bg-white hover:bg-amber-100 border border-amber-300 text-amber-900 font-bold transition-colors"
            >
              Simulate Valid Participant (Pass)
            </button>
            <button
              onClick={() => handleDemoPreset("review")}
              disabled={isInitializing}
              className="px-2.5 py-1 rounded bg-white hover:bg-amber-100 border border-amber-300 text-amber-900 font-bold transition-colors"
            >
              Simulate Duplicate ID (Review)
            </button>
          </div>
        </div>
      )}

      {/* Active Stage Instruction Callout Banner */}
      <div className="p-3.5 rounded-xl bg-surface border border-border flex items-start gap-3 shadow-sm">
        <Info className="w-5 h-5 text-primary shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <p className="text-xs font-serif-display font-bold text-foreground">
            {currentStage === 1 && "STEP 1 OF 3 — PRESENT PHYSICAL ID CARD"}
            {currentStage === 2 && "STEP 2 OF 3 — LOOK AT WEBCAM FOR BIOMETRIC FACE MATCH"}
            {currentStage === 5 && "STEP 3 OF 3 — MAX30102 PULSE SENSOR LIVENESS CHECK"}
            {currentStage >= 7 && "FINAL STEP — AI MULTI-AGENT VERIFICATION & GATE ACTUATION"}
          </p>
          <p className="text-xs text-muted-foreground font-sans">
            {currentStage === 1 && "Hold your college ID card or government credential in front of the camera so the text and photo are clearly visible inside the box, then click 'Capture Exposure'."}
            {currentStage === 2 && "Great! Now position your face inside the oval guide and look directly into the camera lens, then click 'Capture Exposure'."}
            {currentStage === 5 && "Place your fingertip steadily on the MAX30102 pulse sensor (or wait for the waveform acquisition to complete) to prove human liveness."}
            {currentStage >= 7 && "Evidence has been gathered across ID document, biometric embeddings, and pulse sensors. Click below to execute the deterministic decision engine."}
          </p>
        </div>
      </div>

      {/* 8-Stage Pipeline Progress Header */}
      <VerificationProgress currentStage={currentStage} />

      {/* Main Interaction Area */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Interactive Capture & Sensors */}
        <div className="lg:col-span-6 space-y-6">
          {currentStage === 1 ? (
            /* Stage 1: ID Capture */
            <CameraCapture
              mode="document"
              title="Step I: Present Identity Credential"
              subtitle="Hold college ID or government credential steady within the alignment frame"
              onCaptured={handleIdCaptured}
            />
          ) : currentStage === 2 ? (
            /* Stage 2: Selfie Capture */
            <CameraCapture
              mode="selfie"
              title="Step II: Look Toward Optical Sensor"
              subtitle="Center facial features within the oval guide for embedding extraction"
              onCaptured={handleSelfieCaptured}
            />
          ) : currentStage === 5 ? (
            /* Stage 3: Liveness Check */
            <div className="space-y-4">
              <LivenessVisualizer isActive={true} onComplete={handleLivenessDone} />
            </div>
          ) : currentStage >= 7 ? (
            /* Stage 4: Run AI Pipeline / Decision Screen */
            <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-6">
              <div className="text-center">
                <h3 className="text-base font-serif-display font-bold text-foreground">
                  Verification Evaluation
                </h3>
                <p className="text-xs text-muted-foreground font-mono mt-0.5">
                  Multi-agent evidence aggregated across document, embeddings, and pulse sensor
                </p>
              </div>

              {/* Physical Gate State Banner */}
              <div
                className={`p-6 rounded-xl border text-center font-mono transition-all ${
                  gateCommand === "OPEN_GATE"
                    ? "bg-success-surface border-success text-success shadow-md"
                    : "bg-surface border-border text-foreground"
                }`}
              >
                <div className="flex items-center justify-center mb-2">
                  {gateCommand === "OPEN_GATE" ? (
                    <div className="w-12 h-12 rounded-full bg-success/20 text-success flex items-center justify-center">
                      <Unlock className="w-6 h-6" />
                    </div>
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-surface border border-border text-muted-foreground flex items-center justify-center">
                      <Lock className="w-6 h-6" />
                    </div>
                  )}
                </div>
                <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">
                  Physical Turnstile Barrier State
                </p>
                <h2 className="text-xl font-serif-display font-black mt-1">
                  {gateCommand === "OPEN_GATE" ? "SERVO GATE: UNLOCKED (90°)" : "SERVO GATE: SECURED (0°)"}
                </h2>
                <p className="text-xs text-muted-foreground mt-1 font-sans">
                  {gateCommand === "OPEN_GATE"
                    ? "Verification authoritative. Please proceed through the physical gate. Auto-locking in 5 seconds."
                    : "Gate barrier remains locked until authoritative verification passes."}
                </p>
              </div>

              {!finalDecision && (
                <button
                  onClick={handleRunPipeline}
                  disabled={isEvaluating}
                  className="w-full py-3 rounded-lg bg-primary hover:bg-primary-hover text-white font-serif-display font-bold text-xs shadow-md transition-all active:scale-95 flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  {isEvaluating ? "Executing Deterministic AI Pipeline..." : "Execute Verification Pipeline"}
                </button>
              )}
            </div>
          ) : null}
        </div>

        {/* Right Column: Real-Time AI Verification Trace */}
        <div className="lg:col-span-6">
          <AiTracePanel
            agentResults={agentResults}
            finalDecision={finalDecision}
            finalConfidence={finalConfidence}
            finalReasons={finalReasons}
            isDemo={isDemo}
          />
        </div>
      </div>
    </div>
  );
}
