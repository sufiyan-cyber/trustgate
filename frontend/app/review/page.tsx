"use client";

import { useEffect, useState } from "react";
import {
  ClipboardCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Search,
  RefreshCw,
  User,
  Fingerprint,
  FileText,
  HeartPulse,
  ScanFace,
  PlusCircle,
  ShieldAlert,
} from "lucide-react";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/ws";
import { useMode } from "@/context/ModeContext";

export default function AdminReviewPage() {
  const { mode, isLive, isDemo } = useMode();
  const [flaggedSessions, setFlaggedSessions] = useState<any[]>([]);
  const [selectedSession, setSelectedSession] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Modal Action State
  const [actionType, setActionType] = useState<"APPROVE" | "REJECT" | null>(null);
  const [reviewerName, setReviewerName] = useState("admin");
  const [reviewReason, setReviewReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const loadReviews = async () => {
    try {
      setIsLoading(true);
      const data = await api.getFlaggedReviews();
      setFlaggedSessions(data);
      if (data.length > 0 && !selectedSession) {
        setSelectedSession(data[0]);
      } else if (data.length === 0) {
        setSelectedSession(null);
      }
    } catch (err) {
      console.error("Failed to load flagged reviews:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadReviews();

    const unsubscribe = wsClient.subscribe((msg) => {
      if (msg.type === "VERIFICATION_COMPLETE" || msg.type === "ADMIN_REVIEW_ACTION") {
        loadReviews();
      }
    });

    return () => unsubscribe();
  }, []);

  // Demo Helper: Trigger a review case if in Demo Mode and queue is empty
  const handleCreateDemoReviewCase = async (scenarioKey: "B" | "C" | "E") => {
    try {
      setIsLoading(true);
      await api.runDemoScenario(scenarioKey, true);
      await loadReviews();
      setFeedbackMessage(`Demo Scenario ${scenarioKey} dispatched to review queue.`);
    } catch (e: any) {
      console.error("Error creating demo review case:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleActionSubmit = async () => {
    if (!selectedSession || !actionType) return;
    if (!reviewReason.trim()) {
      alert("Please provide a formal audit justification for the access record.");
      return;
    }

    setIsSubmitting(true);
    try {
      if (actionType === "APPROVE") {
        await api.approveReview(selectedSession.session_id, reviewerName, reviewReason);
        setFeedbackMessage(
          `Session #${selectedSession.session_id.slice(0, 8)} approved by ${reviewerName}. Hardware servo gate opened.`
        );
      } else {
        await api.rejectReview(selectedSession.session_id, reviewerName, reviewReason);
        setFeedbackMessage(
          `Session #${selectedSession.session_id.slice(0, 8)} rejected. Physical barrier remains locked.`
        );
      }
      setActionType(null);
      setReviewReason("");
      await loadReviews();
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded border ${
                isLive
                  ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                  : "bg-amber-50 text-amber-800 border-amber-300"
              }`}
            >
              {isLive ? "● LIVE AUDIT QUEUE" : "○ DEMO MODE (Mock Review Fallbacks Available)"}
            </span>
          </div>
          <h1 className="text-2xl font-serif-display font-black text-foreground tracking-tight flex items-center gap-2.5">
            <ClipboardCheck className="w-6 h-6 text-primary" />
            Organizer Verification Review Dossier
          </h1>
          <p className="text-xs text-muted-foreground font-mono">
            Sessions requiring human adjudication prior to physical turnstile servo actuation
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isDemo && (
            <button
              onClick={() => handleCreateDemoReviewCase("B")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-amber-50 text-amber-900 border border-amber-300 text-xs font-mono font-medium hover:bg-amber-100 transition-colors"
            >
              <PlusCircle className="w-3.5 h-3.5 text-primary" />
              Populate Demo Review Case
            </button>
          )}

          <button
            onClick={loadReviews}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-surface border border-border text-xs font-mono text-foreground hover:bg-surface/70 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Queue
          </button>
        </div>
      </div>

      {feedbackMessage && (
        <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs font-mono flex items-center justify-between shadow-sm">
          <span>{feedbackMessage}</span>
          <button onClick={() => setFeedbackMessage(null)} className="text-emerald-700 hover:text-emerald-950 font-bold ml-2">
            ✕
          </button>
        </div>
      )}

      {/* Main Review Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Flagged Sessions List */}
        <div className="lg:col-span-4 bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-2">
            <h2 className="text-xs font-mono font-bold uppercase text-foreground small-caps">
              Flagged Pending Sessions ({flaggedSessions.length})
            </h2>
            <span className="text-[10px] font-mono text-muted-foreground">FIFO Queue</span>
          </div>

          {flaggedSessions.length === 0 ? (
            <div className="py-16 text-center text-muted-foreground text-xs font-sans space-y-2">
              <CheckCircle2 className="w-8 h-8 text-success mx-auto opacity-80" />
              <p className="font-serif-display text-foreground font-semibold">Queue is Clear</p>
              <p className="text-[11px] max-w-xs mx-auto text-muted-foreground">
                No sessions currently require organizer adjudication. All entrants either passed authoritatively or failed hard risk thresholds.
              </p>
              {isDemo && (
                <button
                  onClick={() => handleCreateDemoReviewCase("B")}
                  className="mt-3 px-3 py-1.5 rounded-md bg-surface hover:bg-surface/70 border border-border text-xs font-mono text-foreground"
                >
                  Generate Scenario B (Name Discrepancy)
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[620px] overflow-y-auto pr-1">
              {flaggedSessions.map((s) => {
                const isSelected = selectedSession?.session_id === s.session_id;
                return (
                  <div
                    key={s.session_id}
                    onClick={() => setSelectedSession(s)}
                    className={`p-3.5 rounded-lg border text-left cursor-pointer transition-all ${
                      isSelected
                        ? "bg-amber-50/70 border-primary shadow-sm ring-1 ring-primary/40"
                        : "bg-surface/50 border-border hover:border-border-hover hover:bg-white"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-mono font-bold text-foreground">
                        #{s.session_id.slice(0, 8)}
                      </span>
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-warning-surface text-warning border border-warning/40 font-bold">
                        REVIEW
                      </span>
                    </div>
                    <p className="text-sm font-serif-display font-bold text-foreground">{s.participant_name}</p>
                    <p className="text-xs text-muted-foreground truncate font-sans">{s.institution}</p>
                    <div className="mt-2 text-[10px] font-mono text-muted-foreground flex justify-between pt-1 border-t border-border/50">
                      <span>Node: {s.device_id}</span>
                      <span>Confidence: {Math.round(s.confidence * 100)}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Detailed Evidence Inspection & Decision */}
        <div className="lg:col-span-8 space-y-6">
          {selectedSession ? (
            <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-6">
              {/* Participant Profile Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
                <div className="flex items-center space-x-3.5">
                  <div className="w-12 h-12 rounded-xl bg-surface border border-border flex items-center justify-center text-primary font-bold text-lg">
                    <User className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-lg font-serif-display font-bold text-foreground">
                      {selectedSession.participant_name}
                    </h2>
                    <p className="text-xs text-muted-foreground font-mono">
                      {selectedSession.institution} • {selectedSession.email || "No contact logged"}
                    </p>
                  </div>
                </div>

                {/* Direct Action Buttons */}
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => setActionType("APPROVE")}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-md bg-success hover:bg-success-hover text-white font-serif-display font-bold text-xs shadow-sm transition-all active:scale-95"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Approve & Actuate Gate
                  </button>
                  <button
                    onClick={() => setActionType("REJECT")}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-md bg-danger hover:bg-danger-hover text-white font-serif-display font-bold text-xs shadow-sm transition-all active:scale-95"
                  >
                    <XCircle className="w-4 h-4" />
                    Reject Access
                  </button>
                </div>
              </div>

              {/* Review Justification Reasons */}
              <div className="p-4 rounded-xl bg-warning-surface/60 border border-warning/40">
                <h3 className="text-xs font-mono font-bold uppercase text-warning mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-warning" />
                  Primary System Review Justification
                </h3>
                <div className="space-y-1 text-xs text-foreground font-sans">
                  {selectedSession.reasons?.map((r: string, idx: number) => (
                    <p key={idx} className="flex items-start gap-1.5">
                      <span className="text-warning font-bold">•</span>
                      <span>{r}</span>
                    </p>
                  ))}
                </div>
              </div>

              {/* Multi-Agent Evidence Breakdown Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Duplicate ID Evidence */}
                <div className="p-4 rounded-lg bg-surface/60 border border-border space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-semibold text-foreground flex items-center gap-1.5">
                      <Fingerprint className="w-4 h-4 text-primary" />
                      Duplicate / Reuse Analysis
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-border text-foreground font-medium">
                      {selectedSession.evidence?.duplicate_detection?.decision || "N/A"}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground font-sans leading-relaxed">
                    {selectedSession.evidence?.duplicate_detection?.reason || "No identity conflict detected."}
                  </p>
                  {selectedSession.evidence?.duplicate_detection?.signals?.previous_owner && (
                    <div className="p-2.5 rounded bg-danger-surface border border-danger/30 text-[11px] font-mono text-danger">
                      Conflict: Credential previously registered to:{" "}
                      <strong>
                        {selectedSession.evidence.duplicate_detection.signals.previous_owner}
                      </strong>
                    </div>
                  )}
                </div>

                {/* Face Biometric Evidence */}
                <div className="p-4 rounded-lg bg-surface/60 border border-border space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-semibold text-foreground flex items-center gap-1.5">
                      <ScanFace className="w-4 h-4 text-primary" />
                      Biometric Face Similarity
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-border text-foreground font-medium">
                      {selectedSession.evidence?.identity_matching?.decision || "N/A"}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground font-sans leading-relaxed">
                    {selectedSession.evidence?.identity_matching?.reason || "Biometric comparison complete."}
                  </p>
                  {selectedSession.evidence?.identity_matching?.signals?.face_similarity !== undefined && (
                    <div className="text-xs font-mono text-primary font-bold">
                      Similarity Score:{" "}
                      {Math.round(
                        selectedSession.evidence.identity_matching.signals.face_similarity * 100
                      )}
                      %
                    </div>
                  )}
                </div>

                {/* Document Forensics Evidence */}
                <div className="p-4 rounded-lg bg-surface/60 border border-border space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-semibold text-foreground flex items-center gap-1.5">
                      <FileText className="w-4 h-4 text-primary" />
                      Document Forensics & Integrity
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-border text-foreground font-medium">
                      {selectedSession.evidence?.document_forensics?.decision || "N/A"}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground font-sans leading-relaxed">
                    {selectedSession.evidence?.document_forensics?.reason || "Integrity verified."}
                  </p>
                  {selectedSession.evidence?.document_forensics?.signals?.anomalies?.length > 0 && (
                    <ul className="text-[11px] font-mono text-warning list-disc pl-4 space-y-0.5">
                      {selectedSession.evidence.document_forensics.signals.anomalies.map(
                        (a: string, i: number) => (
                          <li key={i}>{a}</li>
                        )
                      )}
                    </ul>
                  )}
                </div>

                {/* Liveness Sensor Evidence */}
                <div className="p-4 rounded-lg bg-surface/60 border border-border space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-semibold text-foreground flex items-center gap-1.5">
                      <HeartPulse className="w-4 h-4 text-primary" />
                      MAX30102 Pulse Signal
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-border text-foreground font-medium">
                      {selectedSession.evidence?.liveness_verification?.decision || "N/A"}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground font-sans leading-relaxed">
                    {selectedSession.evidence?.liveness_verification?.reason || "Physiological reading evaluated."}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-card border border-border rounded-xl p-16 text-center text-muted-foreground font-serif text-sm">
              Select a flagged session from the left queue to inspect evidence and execute an audited decision.
            </div>
          )}
        </div>
      </div>

      {/* Audit Action Modal */}
      {actionType && selectedSession && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-serif-display font-bold text-foreground flex items-center gap-2">
              {actionType === "APPROVE" ? (
                <CheckCircle2 className="w-5 h-5 text-success" />
              ) : (
                <XCircle className="w-5 h-5 text-danger" />
              )}
              Confirm {actionType} for #{selectedSession.session_id.slice(0, 8)}
            </h3>
            <p className="text-xs text-muted-foreground font-sans leading-relaxed">
              Every manual action requires an organizer identification and a mandatory audit reason. This transaction is cryptographically timestamped in the database.
            </p>

            <div className="space-y-3 text-xs font-sans">
              <div>
                <label className="block text-muted-foreground mb-1 font-mono font-semibold">Reviewer Username</label>
                <input
                  type="text"
                  value={reviewerName}
                  onChange={(e) => setReviewerName(e.target.value)}
                  className="w-full px-3 py-2 rounded-md bg-surface border border-border text-foreground text-xs font-mono focus:border-primary outline-none"
                />
              </div>

              <div>
                <label className="block text-muted-foreground mb-1 font-mono font-semibold">Audit Reason / Justification *</label>
                <textarea
                  rows={3}
                  value={reviewReason}
                  onChange={(e) => setReviewReason(e.target.value)}
                  placeholder="e.g. Inspected physical student card in person; photo matches candidate face."
                  className="w-full px-3 py-2 rounded-md bg-surface border border-border text-foreground text-xs font-sans focus:border-primary outline-none leading-relaxed"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border">
              <button
                onClick={() => setActionType(null)}
                className="px-3.5 py-2 rounded-md bg-surface text-foreground hover:bg-surface/70 text-xs font-mono transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleActionSubmit}
                disabled={isSubmitting}
                className={`px-4 py-2 rounded-md text-white font-serif-display font-bold text-xs transition-all active:scale-95 shadow-sm ${
                  actionType === "APPROVE"
                    ? "bg-success hover:bg-success-hover"
                    : "bg-danger hover:bg-danger-hover"
                }`}
              >
                {isSubmitting ? "Submitting..." : `Confirm ${actionType}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
