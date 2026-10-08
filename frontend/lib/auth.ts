"use client";

import type { AuthResponse, User } from "@/types";

export const TOKEN_KEY = "metroflow_predictor_token";
export const USER_KEY = "metroflow_predictor_user";
const COOKIE_NAME = "metroflow_predictor_token";

export function persistSession(payload: AuthResponse): void {
  if (!payload?.access_token || typeof payload.access_token !== "string") {
    return;
  }
  localStorage.setItem(TOKEN_KEY, payload.access_token.trim());
  localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
  document.cookie = `${COOKIE_NAME}=${payload.access_token.trim()}; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax`;
}

export function clearSession(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    document.cookie = `${COOKIE_NAME}=; path=/; max-age=0; samesite=lax`;
  }
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token || typeof token !== "string") {
    return null;
  }
  const trimmed = token.trim();
  if (trimmed === "" || trimmed.toLowerCase() === "null" || trimmed.toLowerCase() === "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    return null;
  }
  return trimmed;
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function updateStoredUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}
