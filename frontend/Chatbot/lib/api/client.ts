import {
  clearAccessToken,
  getAccessToken,
  isAccessTokenExpiringSoon,
  notifyAuthChange,
  setAccessToken,
} from "@/lib/auth/tokenStorage";

// The backend's origin. The deployed build sets this to an empty string, because the
// backend serves the frontend, so API calls stay on the same origin.
const API_ORIGIN =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export const API_BASE = `${API_ORIGIN}/api`;

export const AUTH_FETCH_INIT: RequestInit = {
  credentials: "include",
};

const REFRESH_LOCK_NAME = "auth-refresh";
const REFRESH_RETRY_DELAY_MS = 300;

type ApiErrorBody = {
  success?: boolean;
  error?: { code?: string; message?: string };
  detail?: string | Array<{ msg?: string }>;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export class ApiRequestError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

export function parseApiError(data: unknown, fallback: string): string {
  if (!data || typeof data !== "object") return fallback;

  const body = data as ApiErrorBody;

  if (body.success === false && body.error?.message) {
    return body.error.message;
  }

  if (typeof body.detail === "string") {
    return body.detail;
  }

  if (Array.isArray(body.detail)) {
    return body.detail
      .map((item) => item?.msg ?? "Validation error")
      .join(", ");
  }

  return fallback;
}

/**
 * Read a JSON response, throwing a typed ApiRequestError (carrying the HTTP
 * status) when the response is not ok. Centralizes the parse/throw boilerplate
 * shared by every API client.
 */
export async function readJson<T>(
  response: Response,
  fallback: string
): Promise<T> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiRequestError(parseApiError(data, fallback), response.status);
  }
  return data as T;
}

let refreshPromise: Promise<string> | null = null;

export async function clearServerSession(): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/clear-session`, {
      ...AUTH_FETCH_INIT,
      method: "POST",
    });
  } catch {
    // Still clear local state when the network call fails.
  }
}

async function endClientSession(): Promise<void> {
  // Only a tab that was logged in announces the change. Otherwise tabs that have
  // already logged out would keep re-verifying and notifying each other.
  const wasLoggedIn = getAccessToken() !== null;
  await clearServerSession();
  clearAccessToken();
  if (wasLoggedIn) {
    notifyAuthChange();
  }
}

async function refreshTokens(canRetry = true): Promise<string> {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    ...AUTH_FETCH_INIT,
    method: "POST",
  });

  // Another request already rotated this token, so the browser now holds a newer
  // cookie. Retrying picks it up, and the session is still valid.
  if (response.status === 409 && canRetry) {
    await new Promise((resolve) => setTimeout(resolve, REFRESH_RETRY_DELAY_MS));
    return refreshTokens(false);
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    // Only a 401 means the session is over. A 500 or a lost race must not log the
    // user out or revoke the session.
    if (response.status === 401) {
      await endClientSession();
    }
    throw new ApiRequestError(
      parseApiError(data, "Session expired. Please log in again."),
      response.status
    );
  }

  const tokens = data as TokenResponse;
  setAccessToken(tokens.access_token);
  return tokens.access_token;
}

async function refreshAcrossTabs(): Promise<string> {
  // navigator.locks only exists on HTTPS and localhost. Without it, a race between
  // tabs is still handled by the 409 retry in refreshTokens.
  if (typeof navigator !== "undefined" && navigator.locks) {
    return navigator.locks.request(REFRESH_LOCK_NAME, () => refreshTokens());
  }
  return refreshTokens();
}

function refreshAccessTokenOnce(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = refreshAcrossTabs().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export async function getValidAccessToken(): Promise<string | null> {
  const accessToken = getAccessToken();

  if (accessToken && !isAccessTokenExpiringSoon()) {
    return accessToken;
  }

  try {
    return await refreshAccessTokenOnce();
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

export async function authenticatedFetch(
  url: string,
  init: RequestInit = {}
): Promise<Response> {
  let token = await getValidAccessToken();
  if (!token) {
    throw new ApiRequestError("Not authenticated", 401);
  }

  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);

  let response = await fetch(url, {
    ...AUTH_FETCH_INIT,
    ...init,
    headers,
  });

  if (response.status === 401) {
    token = await refreshAccessTokenOnce();
    headers.set("Authorization", `Bearer ${token}`);
    response = await fetch(url, {
      ...AUTH_FETCH_INIT,
      ...init,
      headers,
    });
  }

  return response;
}
