import {
  API_BASE,
  ApiRequestError,
  authenticatedFetch,
  readJson,
} from "@/lib/api/authApi";

export type TicketStatus = "pending" | "approved" | "rejected";

export type PendingJiraTicketResponse = {
  id: string;
  user_id: string;
  user_email: string;
  title: string;
  description: string;
  status: TicketStatus;
  created_at: string;
};

export type AdminActionResponse = {
  success: boolean;
  message: string;
  jira_key?: string;
};

export const adminFetcher = async <T = unknown>(url: string): Promise<T> => {
  const res = await authenticatedFetch(url, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  return readJson<T>(res, `Failed to fetch data (${res.status})`);
};

export async function approveTicket(ticketId: string): Promise<AdminActionResponse> {
  const res = await authenticatedFetch(`${API_BASE}/admin/approve-ticket/${ticketId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return readJson<AdminActionResponse>(
    res,
    `Failed to approve ticket (${res.status})`
  );
}

export async function rejectTicket(ticketId: string): Promise<AdminActionResponse> {
  const res = await authenticatedFetch(`${API_BASE}/admin/reject-ticket/${ticketId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return readJson<AdminActionResponse>(
    res,
    `Failed to reject ticket (${res.status})`
  );
}

export type CursorPage<T> = {
  items: T[];
  next_cursor: string | null;
};

export type AdminSummary = {
  pending_tickets: number;
  total_users: number;
  banned_users: number;
  active_sessions: number;
  requests_24h: number;
  failed_requests_24h: number;
};

export type AuditLogEntry = {
  id: string;
  user_id: string | null;
  user_email: string | null;
  method: string;
  path: string;
  status_code: number;
  duration_ms: number;
  ip_address: string | null;
  user_agent: string | null;
  request_id: string | null;
  created_at: string;
};

export type AdminUser = {
  id: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  is_self: boolean;
  active_sessions: number;
  created_at: string;
};

export type AdminSession = {
  id: string;
  ip_address: string | null;
  user_agent: string | null;
  is_current: boolean;
  created_at: string;
  last_rotated_at: string | null;
  expires_at: string;
};

async function adminAction(
  path: string,
  method: "POST" | "DELETE" = "POST"
): Promise<AdminActionResponse> {
  const res = await authenticatedFetch(`${API_BASE}${path}`, { method });
  return readJson<AdminActionResponse>(res, `Request failed (${res.status})`);
}

export const banUser = (userId: string) =>
  adminAction(`/admin/users/${userId}/ban`);

export const unbanUser = (userId: string) =>
  adminAction(`/admin/users/${userId}/unban`);

export const revokeUserSessions = (userId: string) =>
  adminAction(`/admin/users/${userId}/revoke-sessions`);

export const revokeSession = (sessionId: string) =>
  adminAction(`/admin/sessions/${sessionId}`, "DELETE");

export function getAdminErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    if (error.status === 401) {
      return "Your session has expired. Please log in again.";
    }
    if (error.status === 403) {
      return "You need admin permissions to access this dashboard.";
    }
  }

  if (error instanceof Error) {
    if (error.message === "Not authenticated") {
      return "Your session has expired. Please log in again.";
    }
    return error.message;
  }

  return "Failed to load data.";
}
