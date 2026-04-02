"use client";

import { useTheme } from "@/components/ThemeProvider";

const themes = ["light", "dark", "system"] as const;

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="glass-card inline-flex rounded-full p-1">
      {themes.map((item) => (
        <button
          key={item}
          type="button"
          className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize transition ${
            theme === item ? "bg-[var(--accent)] text-white" : "text-[var(--muted)]"
          }`}
          onClick={() => setTheme(item)}
        >
          {item}
        </button>
      ))}
    </div>
  );
}
