"use client";

import type { AuthResponse, User } from "@/types";

export const TOKEN_KEY = "metroflow_predictor_token";
export const USER_KEY = "metroflow_predictor_user";
const COOKIE_NAME = "metroflow_predictor_token";

export function persistSession(payload: AuthResponse): void {
  localStorage.setItem(TOKEN_KEY, payload.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
  document.cookie = `${COOKIE_NAME}=${payload.access_token}; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax`;
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  document.cookie = `${COOKIE_NAME}=; path=/; max-age=0; samesite=lax`;
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem(TOKEN_KEY);
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
