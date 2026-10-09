function resolveBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (envUrl) {
    const stripped = envUrl.replace(/\/+$/, "");
    return stripped.endsWith("/api/v1") ? stripped : `${stripped}/api/v1`;
  }
  if (typeof window !== "undefined") {
    return "/api/v1";
  }
  const backend = process.env.BACKEND_URL?.trim()?.replace(/\/+$/, "");
  if (backend) {
    return backend.endsWith("/api/v1") ? backend : `${backend}/api/v1`;
  }
  return "http://localhost:8000/api/v1";
}

export const API_BASE_URL = resolveBaseUrl();

export class ApiError extends Error {
  status?: number;
  isNetworkError: boolean;
  isAuthError: boolean;

  constructor(message: string, options: { status?: number; isNetworkError?: boolean; isAuthError?: boolean } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = options.status;
    this.isNetworkError = options.isNetworkError ?? false;
    this.isAuthError = options.isAuthError ?? false;
  }
}

async function readResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

export async function apiFetch<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  let response: Response;

  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const baseHeaders: Record<string, string> = {};
  if (!isFormData) {
    baseHeaders["Content-Type"] = "application/json";
  }
  if (token && typeof token === "string") {
    const cleanToken = token.trim();
    if (cleanToken && cleanToken.toLowerCase() !== "null" && cleanToken.toLowerCase() !== "undefined") {
      baseHeaders["Authorization"] = `Bearer ${cleanToken}`;
    }
  }

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...baseHeaders,
        ...(options.headers ?? {})
      },
      cache: "no-store"
    });
  } catch {
    throw new ApiError(`Cannot reach the backend at ${API_BASE_URL}. Start the FastAPI server and try again.`, {
      isNetworkError: true
    });
  }

  if (!response.ok) {
    if (response.status === 401 && typeof window !== "undefined") {
      try {
        localStorage.removeItem("metroflow_predictor_token");
        localStorage.removeItem("metroflow_predictor_user");
        document.cookie = "metroflow_predictor_token=; path=/; max-age=0; samesite=lax";
      } catch {
        // ignore storage errors
      }
    }

    const payload = await readResponseBody(response);
    const message =
      typeof payload === "string"
        ? payload
        : typeof payload === "object" && payload !== null && "detail" in payload
          ? String(payload.detail)
          : "Request failed";

    throw new ApiError(message, {
      status: response.status,
      isAuthError: response.status === 401 || response.status === 403
    });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return readResponseBody(response) as Promise<T>;
}
