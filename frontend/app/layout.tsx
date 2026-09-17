import type { Metadata } from "next";
import { Playfair_Display, Source_Sans_3, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { ModeProvider } from "@/context/ModeContext";

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

const sourceSans = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-source-sans",
  display: "swap",
});

const ibmPlexMono = IBM_Plex_Mono({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-ibm-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "TRUST GATE | AI Physical Identity & Access Gateway",
  description: "Publication-Grade Biometric & Document Verification System with Physical Turnstile Actuation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${playfair.variable} ${sourceSans.variable} ${ibmPlexMono.variable}`}>
      <body className="min-h-screen bg-background text-foreground antialiased flex flex-col font-sans selection:bg-accent/20 selection:text-accent">
        <ModeProvider>
          <Navbar />
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
          <footer className="border-t border-border bg-white/70 py-6 text-center text-xs font-mono text-muted-foreground">
            <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
              <span className="font-serif tracking-wide text-foreground/80 font-medium">
                TRUST GATE • Vol. I • Physical Security & Identity Verification
              </span>
              <span className="text-[11px] tracking-wider text-muted-foreground">
                ESP32 (PWM GPIO25) • AWS Textract • Deep Biometrics • Hackingly AI 2026
              </span>
            </div>
          </footer>
        </ModeProvider>
      </body>
    </html>
  );
}
