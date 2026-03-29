import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          deep: "#0a0a0f",
          dark: "#1a1a2e",
          card: "#16213e",
          hover: "#1f2b4a",
        },
        accent: {
          gold: "#d4a44a",
          "gold-light": "#e8c272",
        },
        enemy: {
          boss: "#c0392b",
          "boss-bg": "#2d1b1b",
          elite: "#8e44ad",
          "elite-bg": "#2a1a3a",
          normal: "#555e6b",
          "normal-bg": "#1e232b",
        },
        text: {
          primary: "#e0e0e0",
          secondary: "#a0a0b0",
          muted: "#606070",
        },
      },
      fontFamily: {
        sans: ["Noto Serif JP", "Georgia", "serif"],
        mono: ["Noto Sans JP", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
