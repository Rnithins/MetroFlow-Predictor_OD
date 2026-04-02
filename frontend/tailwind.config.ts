import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        mist: "#e2e8f0",
        signal: "#0f766e",
        warning: "#b45309",
        panel: "#f8fafc"
      },
      boxShadow: {
        panel: "0 20px 50px rgba(15, 23, 42, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
