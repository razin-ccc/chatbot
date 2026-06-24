import { clearActiveConversationId } from "@/lib/auth/conversationStorage";
import {
  clearTokens,
  getStoredAccessToken,
  isAccessTokenExpiringSoon,
  persistAccessToken,
  subscribeAuthChanges,
} from "@/lib/auth/tokenStorage";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export { subscribeAuthChanges };

type ApiErrorBody = {
  success?: boolean;
  error?: { code?: string; message?: string };
  detail?: string | Array<{ msg?: string }>;
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

type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type UserMe = {
  id: string;
  email: string;
  permissions: string[];
};

const AUTH_FETCH_INIT: RequestInit = {
  credentials: "include",
};

let refreshPromise: Promise<string> | null = null;

async function clearServerSession(): Promise<void> {
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
  await clearServerSession();
  clearTokens();
}

async function refreshTokens(): Promise<string> {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    ...AUTH_FETCH_INIT,
    method: "POST",
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    await endClientSession();
    throw new Error(
      parseApiError(data, "Session expired. Please log in again.")
    );
  }

  const tokens = data as TokenResponse;
  persistAccessToken(tokens.access_token);
  return tokens.access_token;
}

export async function getValidAccessToken(): Promise<string | null> {
  const accessToken = getStoredAccessToken();

  if (accessToken && !isAccessTokenExpiringSoon()) {
    return accessToken;
  }

  if (!refreshPromise) {
    refreshPromise = refreshTokens().finally(() => {
      refreshPromise = null;
    });
  }

  try {
    return await refreshPromise;
  } catch {
    return null;
  }
}

export async function fetchCurrentUser(): Promise<UserMe> {
  const token = await getValidAccessToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(`${API_BASE}/auth/me`, {
    ...AUTH_FETCH_INIT,
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 401) {
      await endClientSession();
    }
    throw new Error(parseApiError(data, "Failed to verify session"));
  }

  return data as UserMe;
}

export async function authenticatedFetch(
  url: string,
  init: RequestInit = {}
): Promise<Response> {
  let token = await getValidAccessToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);

  let response = await fetch(url, {
    ...AUTH_FETCH_INIT,
    ...init,
    headers,
  });

  if (response.status === 401) {
    if (!refreshPromise) {
      refreshPromise = refreshTokens().finally(() => {
        refreshPromise = null;
      });
    }

    try {
      token = await refreshPromise;
      headers.set("Authorization", `Bearer ${token}`);
      response = await fetch(url, {
        ...AUTH_FETCH_INIT,
        ...init,
        headers,
      });
    } catch {
      await endClientSession();
      throw new Error("Session expired. Please log in again.");
    }
  }

  return response;
}

export async function logout(): Promise<void> {
  const accessToken = getStoredAccessToken();

  try {
    if (accessToken) {
      await fetch(`${API_BASE}/auth/logout`, {
        ...AUTH_FETCH_INIT,
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
    } else {
      await clearServerSession();
    }
  } catch {
    await clearServerSession();
  }

  clearTokens();
  clearActiveConversationId();
}

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const response = await fetch(`${API_BASE}/auth/login`, {
    ...AUTH_FETCH_INIT,
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData.toString(),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(parseApiError(data, "Login failed"));
  }

  const tokens = data as TokenResponse;
  clearActiveConversationId();
  persistAccessToken(tokens.access_token);
  return tokens;
}

export async function register(
  email: string,
  password: string
): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(parseApiError(data, "Registration failed"));
  }
}
