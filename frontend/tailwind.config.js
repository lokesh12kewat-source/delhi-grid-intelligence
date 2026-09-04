/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        cyber: {
          cyan:   "#00ffff",
          blue:   "#00a2ff",
          green:  "#00ff88",
          red:    "#ff3366",
          yellow: "#ffcc00",
          orange: "#ff6600",
        },
        grid: {
          900: "#060a14",
          800: "#0a0f1e",
          700: "#0f1828",
          600: "#1a2540",
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "pulse-red":   "pulse-red 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "pulse-slow":  "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow-cyan":   "glow-cyan 2s ease-in-out infinite alternate",
        "spin-slow":   "spin 8s linear infinite",
      },
      keyframes: {
        "pulse-red": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(255,51,102,0.4)" },
          "50%":      { boxShadow: "0 0 0 12px rgba(255,51,102,0)" },
        },
        "glow-cyan": {
          "0%":   { boxShadow: "0 0 5px rgba(0,255,255,0.3)" },
          "100%": { boxShadow: "0 0 20px rgba(0,255,255,0.8)" },
        },
      },
      backdropBlur: { glass: "16px" },
    },
  },
  plugins: [],
}
