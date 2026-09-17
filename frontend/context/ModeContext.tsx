"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export type SystemMode = "LIVE" | "DEMO";

interface ModeContextType {
  mode: SystemMode;
  isLive: boolean;
  isDemo: boolean;
  setMode: (mode: SystemMode) => void;
  toggleMode: () => void;
}

const ModeContext = createContext<ModeContextType | undefined>(undefined);

export function ModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<SystemMode>("LIVE");

  useEffect(() => {
    const saved = localStorage.getItem("trustgate_mode") as SystemMode | null;
    if (saved === "LIVE" || saved === "DEMO") {
      setModeState(saved);
    }
  }, []);

  const setMode = (newMode: SystemMode) => {
    setModeState(newMode);
    try {
      localStorage.setItem("trustgate_mode", newMode);
    } catch (e) {
      console.warn("Could not persist mode to localStorage:", e);
    }
  };

  const toggleMode = () => {
    setMode(mode === "LIVE" ? "DEMO" : "LIVE");
  };

  return (
    <ModeContext.Provider
      value={{
        mode,
        isLive: mode === "LIVE",
        isDemo: mode === "DEMO",
        setMode,
        toggleMode,
      }}
    >
      {children}
    </ModeContext.Provider>
  );
}

export function useMode() {
  const context = useContext(ModeContext);
  if (!context) {
    throw new Error("useMode must be used within a ModeProvider");
  }
  return context;
}
