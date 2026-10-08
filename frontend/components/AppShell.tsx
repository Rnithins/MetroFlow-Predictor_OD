"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ThemeToggle } from "@/components/ThemeToggle";
import { clearSession, getStoredUser } from "@/lib/auth";
import { getInitials } from "@/lib/format";
import type { User } from "@/types";

type AppShellProps = {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
};

const items = [
  { href: "/dashboard", label: "Overview", exact: true },
  { href: "/dashboard/india", label: "National Portal" },
  { href: "/dashboard/city", label: "Metro Networks" },
  { href: "/dashboard/od-network", label: "OD Matrix & Graph" },
  { href: "/dashboard/gtfs", label: "GTFS Pipeline" },
  { href: "/dashboard/route-optimization", label: "Route Optimizer" },
  { href: "/dashboard/predictions", label: "AI Forecasts" },
  { href: "/dashboard/simulation", label: "Operations Simulator" },
  { href: "/dashboard/reports", label: "Reports" },
  { href: "/profile", label: "Profile" },
  { href: "/admin", label: "Admin", adminOnly: true }
];

export function AppShell({
  title = "MetroFlow Predictor",
  subtitle = "AI-Driven Origin-Destination Passenger Intelligence",
  children,
  actions
}: AppShellProps) {
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
      {/* ── Apple Floating Frosted Island Header ── */}
      <header className="glass-card mb-8 p-4 sm:p-5 transition-all duration-300">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          
          {/* Brand Monogram & Title */}
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 p-[1px] shadow-lg shadow-blue-500/20">
              <div className="flex h-full w-full items-center justify-center rounded-[15px] bg-white/20 backdrop-blur-md">
                <span className="text-sm font-bold tracking-wider text-white">MF</span>
              </div>
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500 border border-white/60 dark:border-black/60" />
              </span>
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">
                  MetroFlowNet · Transit OS
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-blue-500/10 dark:bg-blue-400/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--accent)] border border-blue-500/20">
                  <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
                  AFFN v2.4
                </span>
              </div>
              <h1 className="truncate text-lg sm:text-2xl font-bold tracking-tight text-[var(--text)]">
                {title}
              </h1>
              <p className="truncate text-xs text-[var(--muted)]">
                {subtitle}
              </p>
            </div>
          </div>

          {/* Right Controls: Theme Toggle & User Pill */}
          <div className="flex shrink-0 items-center gap-2.5 self-start sm:self-center">
            <ThemeToggle />

            <div className="flex items-center gap-2.5 rounded-full border border-[var(--panel-border)] bg-black/[0.03] dark:bg-white/[0.06] p-1 pr-3 backdrop-blur-md shadow-sm">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-tr from-blue-500 to-indigo-500 text-[11px] font-bold text-white shadow-sm">
                {user ? getInitials(user.full_name) : "MF"}
              </div>
              <div className="hidden text-left md:block">
                <p className="text-xs font-semibold leading-tight text-[var(--text)]">
                  {user?.full_name ?? "Transit Analyst"}
                </p>
                <p className="text-[9px] uppercase tracking-wider text-[var(--muted)] font-medium">
                  {user?.role ?? "Operator"}
                </p>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="ml-1 rounded-full px-2 py-0.5 text-[11px] font-medium text-[var(--muted)] hover:bg-red-500/10 hover:text-[var(--danger)] transition-all"
                title="Sign out"
              >
                Exit
              </button>
            </div>
          </div>
        </div>

        {/* Specular Hairline Divider */}
        <div className="my-3.5 h-[1px] w-full bg-gradient-to-r from-transparent via-[var(--panel-border)] to-transparent opacity-80" />

        {/* Cupertino Segmented Navigation Pill Strip */}
        <nav className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5">
          <div className="apple-segmented-track w-full overflow-x-auto no-scrollbar justify-start">
            {visibleItems.map((item) => {
              const isActive = item.exact
                ? pathname === item.href
                : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`apple-segmented-item whitespace-nowrap ${
                    isActive ? "active" : ""
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>
      </header>

      {actions && (
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div />
          {actions}
        </div>
      )}

      {children}
    </main>
  );
}
