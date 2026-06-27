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

  return "Failed to load tickets.";
}
