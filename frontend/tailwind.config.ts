import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0f19",
        mist: "#f4f6fa",
        apple: {
          blue: "#0071e3",
          blueHover: "#0077ed",
          indigo: "#5856d6",
          purple: "#af52de",
          pink: "#ff2d55",
          teal: "#06b6d4",
          emerald: "#10b981",
          amber: "#f59e0b",
          red: "#ef4444",
          surface: "rgba(255, 255, 255, 0.72)",
          surfaceDark: "rgba(18, 24, 38, 0.65)",
        }
      },
      borderRadius: {
        "apple-sm": "10px",
        "apple": "18px",
        "apple-lg": "24px",
        "apple-xl": "32px",
      },
      backdropBlur: {
        apple: "28px",
        "apple-heavy": "40px",
      },
      boxShadow: {
        "apple-glass-light": "0 10px 30px -5px rgba(0, 0, 0, 0.04), 0 20px 40px -10px rgba(0, 113, 227, 0.05), inset 0 1px 1px 0 rgba(255, 255, 255, 0.8), inset 0 0 0 1px rgba(255, 255, 255, 0.5)",
        "apple-glass-dark": "0 20px 50px -10px rgba(0, 0, 0, 0.6), 0 0 30px -5px rgba(0, 113, 227, 0.12), inset 0 1px 1px 0 rgba(255, 255, 255, 0.14), inset 0 0 0 1px rgba(255, 255, 255, 0.06)",
        "apple-btn": "0 8px 20px -4px rgba(0, 113, 227, 0.4), inset 0 1px 1px 0 rgba(255, 255, 255, 0.35)",
        "apple-card-hover": "0 24px 60px -12px rgba(0, 0, 0, 0.25), 0 0 40px -8px rgba(0, 113, 227, 0.2)",
      },
      animation: {
        "pulse-subtle": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "float": "float 6s ease-in-out infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
        }
      }
    }
  },
  plugins: []
};

export default config;
