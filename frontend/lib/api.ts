export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

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

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
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
