const ACCESS_TOKEN_KEY = "access_token";
const ACCESS_EXPIRY_KEY = "access_token_expiry";
const AUTH_CHANNEL_NAME = "auth";
export const SESSION_COOKIE = "has_session";

const REFRESH_BUFFER_MS = 60_000;
const SESSION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60;

function parseJwtExpiry(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return typeof payload.exp === "number" ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getAccessTokenExpiry(): number {
  if (typeof window === "undefined") return 0;
  return Number(localStorage.getItem(ACCESS_EXPIRY_KEY) ?? 0);
}

export function isAccessTokenExpiringSoon(): boolean {
  const expiry = getAccessTokenExpiry();
  if (!expiry) return true;
  return Date.now() >= expiry - REFRESH_BUFFER_MS;
}

export function notifyAuthChange(): void {
  if (typeof window === "undefined") return;

  window.dispatchEvent(new Event("auth-changed"));

  try {
    const channel = new BroadcastChannel(AUTH_CHANNEL_NAME);
    channel.postMessage({ type: "auth-changed" });
    channel.close();
  } catch {
    // BroadcastChannel is not available in every environment.
  }
}

export function setFrontendSessionCookie(): void {
  if (typeof document === "undefined") return;

  const secure = window.location.protocol === "https:" ? "; secure" : "";
  document.cookie = `${SESSION_COOKIE}=1; path=/; max-age=${SESSION_MAX_AGE_SECONDS}; samesite=lax${secure}`;
}

export function clearFrontendSessionCookie(): void {
  if (typeof document === "undefined") return;

  const secure = window.location.protocol === "https:" ? "; secure" : "";
  document.cookie = `${SESSION_COOKIE}=; path=/; max-age=0; samesite=lax${secure}`;
}

export function persistAccessToken(accessToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);

  const expiry = parseJwtExpiry(accessToken);
  if (expiry) {
    localStorage.setItem(ACCESS_EXPIRY_KEY, String(expiry));
  }

  setFrontendSessionCookie();
  notifyAuthChange();
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(ACCESS_EXPIRY_KEY);
  clearFrontendSessionCookie();
  notifyAuthChange();
}

export function hasStoredSession(): boolean {
  return Boolean(getStoredAccessToken());
}

export function subscribeAuthChanges(listener: () => void): () => void {
  if (typeof window === "undefined") {
    return () => undefined;
  }

  const onAuthChanged = () => listener();

  window.addEventListener("auth-changed", onAuthChanged);

  let channel: BroadcastChannel | null = null;
  try {
    channel = new BroadcastChannel(AUTH_CHANNEL_NAME);
    channel.onmessage = () => listener();
  } catch {
    channel = null;
  }

  return () => {
    window.removeEventListener("auth-changed", onAuthChanged);
    channel?.close();
  };
}
