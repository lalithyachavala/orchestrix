import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b0d12",
        panel: "#141821",
        panel2: "#1b212d",
        edge: "#273041",
        ink: "#e7ecf3",
        sub: "#93a0b4",
        brand: "#6ea8ff",
        ok: "#4ade80",
        warn: "#fbbf24",
        bad: "#f87171",
        sens: "#c084fc",
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
