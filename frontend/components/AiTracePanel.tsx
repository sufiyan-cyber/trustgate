"use client";

import { CheckCircle2, AlertTriangle, XCircle, Clock, ShieldCheck } from "lucide-react";

interface AgentResult {
  agent: string;
  status: "SUCCESS" | "INCONCLUSIVE" | "ERROR";
  decision: "PASS" | "REVIEW" | "FAIL";
  confidence: number;
  severity: "LOW" | "MEDIUM" | "HIGH";
  reasons: string[];
  signals: Record<string, any>;
}

interface AiTracePanelProps {
  agentResults?: AgentResult[];
  finalDecision?: "PASS" | "REVIEW" | "FAIL" | null;
  finalConfidence?: number;
  finalReasons?: string[];
  isDemo?: boolean;
}

export default function AiTracePanel({
  agentResults = [],
  finalDecision = null,
  finalConfidence = 0.0,
  finalReasons = [],
  isDemo = false,
}: AiTracePanelProps) {
  const agentMap = new Map(agentResults.map((r) => [r.agent, r]));

  const traceSteps = [
    {
      num: "I",
      id: "document_extraction",
      name: "Document Extraction Agent",
      provider: "AWS Textract Primary",
      result: agentMap.get("document_extraction"),
    },
    {
      num: "II",
      id: "document_forensics",
      name: "Document Forensics Agent",
      provider: "Image ELA & Spectral Anomaly Engine",
      result: agentMap.get("document_forensics"),
    },
    {
      num: "III",
      id: "identity_matching",
      name: "Identity Matching Agent",
      provider: "Deep Face Embedding + Jaro-Winkler",
      result: agentMap.get("identity_matching"),
    },
    {
      num: "IV",
      id: "duplicate_detection",
      name: "Duplicate Detection Agent",
      provider: "Cryptographic SHA256 Lookup",
      result: agentMap.get("duplicate_detection"),
    },
    {
      num: "V",
      id: "liveness_verification",
      name: "Liveness Verification Agent",
      provider: "MAX30102 Physiological Telemetry",
      result: agentMap.get("liveness_verification"),
    },
    {
      num: "VI",
      id: "eligibility_evaluation",
      name: "Eligibility Evaluation Agent",
      provider: "Hackingly Deterministic Rule Engine",
      result: agentMap.get("eligibility_evaluation"),
    },
  ];

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-md relative overflow-hidden">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-border">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-serif-display font-bold text-foreground">
              Verification Audit & Evidence Dossier
            </h3>
            {isDemo && (
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-warning-surface text-warning border border-warning/40 font-semibold">
                Simulated Dossier
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground font-mono mt-0.5">
            Multi-Agent Deterministic Decision Architecture
          </p>
        </div>

        {finalDecision && (
          <div
            className={`px-3.5 py-1.5 rounded-md text-xs font-mono font-bold tracking-wide flex items-center space-x-1.5 border ${
              finalDecision === "PASS"
                ? "bg-success-surface text-success border-success/30"
                : finalDecision === "REVIEW"
                ? "bg-warning-surface text-warning border-warning/30"
                : "bg-danger-surface text-danger border-danger/30"
            }`}
          >
            <span>DECISION: {finalDecision}</span>
            <span>({Math.round(finalConfidence * 100)}%)</span>
          </div>
        )}
      </div>

      {/* Agents Execution Trace (I - VI) */}
      <div className="space-y-3 font-mono text-xs">
        {traceSteps.map((step) => {
          const res = step.result;
          const isFinished = !!res;
          const isPass = res?.decision === "PASS";
          const isReview = res?.decision === "REVIEW";

          return (
            <div
              key={step.id}
              className={`p-3.5 rounded-lg border transition-all ${
                !isFinished
                  ? "bg-surface/50 border-border/70 text-muted-foreground"
                  : isPass
                  ? "bg-success-surface/40 border-success/30 text-foreground"
                  : isReview
                  ? "bg-warning-surface/40 border-warning/30 text-foreground"
                  : "bg-danger-surface/40 border-danger/30 text-foreground"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <span className="font-serif-display font-bold text-xs w-5 text-muted-foreground">
                    {step.num}.
                  </span>
                  {!isFinished ? (
                    <Clock className="w-4 h-4 text-muted-foreground/60" />
                  ) : isPass ? (
                    <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
                  ) : isReview ? (
                    <AlertTriangle className="w-4 h-4 text-warning shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-danger shrink-0" />
                  )}
                  <span className="font-semibold text-foreground font-sans">
                    {step.name}
                  </span>
                  <span className="hidden sm:inline text-[10px] text-muted-foreground">
                    [{step.provider}]
                  </span>
                </div>

                {isFinished && (
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded border ${
                      isPass
                        ? "text-success border-success/30 bg-white"
                        : isReview
                        ? "text-warning border-warning/30 bg-white"
                        : "text-danger border-danger/30 bg-white"
                    }`}
                  >
                    {res.decision} ({Math.round(res.confidence * 100)}%)
                  </span>
                )}
              </div>

              {/* Granular agent reasons / signals */}
              {isFinished && res.reasons.length > 0 && (
                <div className="mt-2 pl-8 space-y-1 text-foreground/80 font-sans text-xs">
                  {res.reasons.slice(0, 2).map((reason, rIdx) => (
                    <div key={rIdx} className="flex items-start space-x-1.5">
                      <span className="text-primary font-mono select-none">└─</span>
                      <span className="leading-snug">{reason}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Classical Verdict Seal Box */}
      {finalDecision && (
        <div
          className={`mt-5 p-5 rounded-xl border text-center relative ${
            finalDecision === "PASS"
              ? "bg-success-surface/50 border-success/40 text-success"
              : finalDecision === "REVIEW"
              ? "bg-warning-surface/50 border-warning/40 text-warning"
              : "bg-danger-surface/50 border-danger/40 text-danger"
          }`}
        >
          <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground mb-1">
            Authoritative Verification Certificate
          </p>
          <h2 className="text-xl font-serif-display font-black tracking-tight text-foreground">
            {finalDecision === "PASS"
              ? "✓ APPROVED — PHYSICAL ACCESS GRANTED"
              : finalDecision === "REVIEW"
              ? "⚠ DESK REVIEW REQUIRED — GATE SECURED"
              : "✕ VERIFICATION REJECTED — ACCESS DENIED"}
          </h2>
          <p className="text-xs text-muted-foreground mt-1 font-mono">
            Aggregate Confidence: {Math.round(finalConfidence * 100)}% • Policy Risk:{" "}
            {finalDecision === "PASS" ? "MINIMAL" : "ELEVATED"}
          </p>

          {/* Structured reason list */}
          {finalReasons.length > 0 && (
            <div className="mt-3 pt-3 border-t border-border/80 text-left font-sans text-xs space-y-1 text-foreground">
              {finalReasons.map((fr, idx) => (
                <p key={idx} className="flex items-start gap-1.5">
                  <span className="text-muted-foreground font-mono">•</span>
                  <span>{fr}</span>
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
