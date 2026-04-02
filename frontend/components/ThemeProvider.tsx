"use client";

import { createContext, useContext, useEffect, useState } from "react";

import type { ThemePreference } from "@/types";

type ThemeContextValue = {
  theme: ThemePreference;
  resolvedTheme: "light" | "dark";
  setTheme: (theme: ThemePreference) => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);
const STORAGE_KEY = "metroflow_predictor_theme";

function resolveTheme(theme: ThemePreference): "light" | "dark" {
  if (theme === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return theme;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemePreference>("system");
  const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const storedTheme = (localStorage.getItem(STORAGE_KEY) as ThemePreference | null) ?? "system";
    const nextResolvedTheme = resolveTheme(storedTheme);
    document.documentElement.dataset.theme = nextResolvedTheme;
    setThemeState(storedTheme);
    setResolvedTheme(nextResolvedTheme);

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      const currentTheme = (localStorage.getItem(STORAGE_KEY) as ThemePreference | null) ?? "system";
      const currentResolvedTheme = resolveTheme(currentTheme);
      document.documentElement.dataset.theme = currentResolvedTheme;
      setResolvedTheme(currentResolvedTheme);
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  function setTheme(nextTheme: ThemePreference) {
    localStorage.setItem(STORAGE_KEY, nextTheme);
    const nextResolvedTheme = resolveTheme(nextTheme);
    document.documentElement.dataset.theme = nextResolvedTheme;
    setThemeState(nextTheme);
    setResolvedTheme(nextResolvedTheme);
  }

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}
