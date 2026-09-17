"use client";

import { Check } from "lucide-react";

interface VerificationProgressProps {
  currentStage: number; // 1 to 8
}

const STAGES = [
  { num: "I", label: "Present ID" },
  { num: "II", label: "Extract" },
  { num: "III", label: "Forensics" },
  { num: "IV", label: "Biometrics" },
  { num: "V", label: "Liveness" },
  { num: "VI", label: "Duplicate" },
  { num: "VII", label: "Eligibility" },
  { num: "VIII", label: "Verdict" },
];

export default function VerificationProgress({ currentStage }: VerificationProgressProps) {
  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-sm font-mono">
      <div className="flex items-center justify-between text-xs text-muted-foreground mb-3 pb-2 border-b border-border">
        <span className="font-serif-display font-semibold uppercase tracking-wider text-foreground">
          Verification Sequence
        </span>
        <span className="text-primary font-bold">
          STAGE 0{Math.min(currentStage, 8)} OF 08
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
        {STAGES.map((s, idx) => {
          const stageNum = idx + 1;
          const isDone = stageNum < currentStage;
          const isCurrent = stageNum === currentStage;

          return (
            <div
              key={stageNum}
              className={`p-2 rounded-lg border text-center transition-all ${
                isDone
                  ? "bg-success-surface/40 border-success/40 text-success"
                  : isCurrent
                  ? "bg-amber-50 border-primary text-foreground font-bold shadow-sm"
                  : "bg-surface/60 border-border/70 text-muted-foreground/60"
              }`}
            >
              <div className="flex items-center justify-center gap-1 text-[11px] mb-0.5">
                {isDone ? (
                  <Check className="w-3.5 h-3.5 text-success" />
                ) : (
                  <span className="font-serif-display font-bold">{s.num}</span>
                )}
              </div>
              <p className="text-[10px] leading-tight truncate">{s.label}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
