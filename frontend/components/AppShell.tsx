"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ThemeToggle } from "@/components/ThemeToggle";
import { clearSession, getStoredUser } from "@/lib/auth";
import { getInitials } from "@/lib/format";
import type { User } from "@/types";

type AppShellProps = {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
};

const items = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/history", label: "History" },
  { href: "/profile", label: "Profile" },
  { href: "/admin", label: "Admin", adminOnly: true }
];

export function AppShell({ title, subtitle, children, actions }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, []);

  const visibleItems = items.filter((item) => !item.adminOnly || user?.role === "admin");

  function handleLogout() {
    clearSession();
    router.push("/auth");
    router.refresh();
  }

  return (
    <main className="app-shell">
      <div className="mb-5 flex flex-col gap-4 rounded-[30px] border border-[var(--panel-border)] bg-[color:var(--panel)] p-4 backdrop-blur-xl lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--accent)]/15 text-lg font-bold text-[var(--accent)]">
            M
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[var(--muted)]">MetroFlow Predictor</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-[-0.03em]">{title}</h1>
            <p className="text-sm text-[var(--muted)]">{subtitle}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <nav className="glass-card inline-flex flex-wrap rounded-full p-1">
            {visibleItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    isActive ? "bg-[var(--accent)] text-white" : "text-[var(--muted)]"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <ThemeToggle />
          <div className="glass-card flex items-center gap-3 rounded-full px-3 py-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--accent-soft)] text-sm font-bold text-[var(--accent)]">
              {user ? getInitials(user.full_name) : "MF"}
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-semibold">{user?.full_name ?? "Metro User"}</p>
              <p className="text-xs text-[var(--muted)]">{user?.role ?? "guest"}</p>
            </div>
            <button type="button" onClick={handleLogout} className="button-ghost px-2 py-0 text-xs">
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="mb-6 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div />
        {actions}
      </div>

      {children}
    </main>
  );
}
