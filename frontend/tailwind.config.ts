import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#FAFAF8",
        foreground: "#1A1A1A",
        surface: "#F5F3F0",
        card: {
          DEFAULT: "#FFFFFF",
          hover: "#FDFCFB",
        },
        border: {
          DEFAULT: "#E8E4DF",
          hover: "#C8C3BA",
        },
        primary: {
          DEFAULT: "#B8860B",
          hover: "#996D09",
          foreground: "#FFFFFF",
        },
        accent: {
          DEFAULT: "#B8860B",
          secondary: "#D4A84B",
          muted: "rgba(184, 134, 11, 0.08)",
          foreground: "#FFFFFF",
        },
        muted: {
          DEFAULT: "#F5F3F0",
          foreground: "#6B6B6B",
        },
        success: {
          DEFAULT: "#2D6A4F",
          hover: "#1B4332",
          surface: "#EBF5EE",
          foreground: "#FFFFFF",
        },
        warning: {
          DEFAULT: "#B8860B",
          hover: "#996D09",
          surface: "#FDF8ED",
          foreground: "#FFFFFF",
        },
        danger: {
          DEFAULT: "#9B2226",
          hover: "#701A1D",
          surface: "#FBEBEB",
          foreground: "#FFFFFF",
        },
      },
      fontFamily: {
        serif: ["var(--font-playfair)", "Georgia", "serif"],
        sans: ["var(--font-source-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-ibm-mono)", "monospace"],
      },
      boxShadow: {
        sm: "0 1px 2px rgba(26, 26, 26, 0.04)",
        md: "0 4px 12px rgba(26, 26, 26, 0.06)",
        lg: "0 8px 24px rgba(26, 26, 26, 0.08)",
        accent: "0 4px 14px rgba(184, 134, 11, 0.20)",
      },
      lineHeight: {
        relaxed: "1.75",
      },
    },
  },
  plugins: [],
};
export default config;
