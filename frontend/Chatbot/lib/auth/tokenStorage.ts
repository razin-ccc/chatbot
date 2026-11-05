const AUTH_CHANNEL_NAME = "auth";
const REFRESH_BUFFER_MS = 60_000;

// Kept in memory so an XSS payload can't read it from storage. Each tab holds its own
// copy, and a reload gets a new one from the HttpOnly refresh cookie.
let accessToken: string | null = null;
let accessTokenExpiry = 0;

function parseJwtExpiry(token: string): number {
  try {
    // JWTs use base64url, which atob can't decode directly.
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const payload = JSON.parse(atob(base64));
    return typeof payload.exp === "number" ? payload.exp * 1000 : 0;
  } catch {
    return 0;
  }
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string): void {
  accessToken = token;
  accessTokenExpiry = parseJwtExpiry(token);
}

export function clearAccessToken(): void {
  accessToken = null;
  accessTokenExpiry = 0;
}

export function isAccessTokenExpiringSoon(): boolean {
  return Date.now() >= accessTokenExpiry - REFRESH_BUFFER_MS;
}

/** Tell this tab and the others that the user logged in or out. */
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
