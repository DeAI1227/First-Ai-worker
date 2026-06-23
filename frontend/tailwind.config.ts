import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "hsl(var(--bg))",
        surface: "hsl(var(--surface))",
        surface2: "hsl(var(--surface-2))",
        border: "hsl(var(--border))",
        text: "hsl(var(--text))",
        muted: "hsl(var(--muted))",
        accent: "hsl(var(--accent))",
        accent2: "hsl(var(--accent-2))",
        critical: "hsl(var(--critical))",
        important: "hsl(var(--important))",
        general: "hsl(var(--general))",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(94, 234, 212, 0.14), 0 20px 50px rgba(15, 23, 42, 0.55)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
      },
      backgroundImage: {
        "grid-faint":
          "linear-gradient(rgba(148,163,184,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.08) 1px, transparent 1px)",
        "accent-radial":
          "radial-gradient(circle at top left, rgba(45,212,191,0.12), transparent 45%), radial-gradient(circle at top right, rgba(99,102,241,0.12), transparent 40%)",
      },
    },
  },
  plugins: [],
} satisfies Config;
