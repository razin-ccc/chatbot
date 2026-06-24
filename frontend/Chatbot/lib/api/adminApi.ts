import {
  API_BASE,
  ApiRequestError,
  authenticatedFetch,
  parseApiError,
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

export const adminFetcher = async (url: string) => {
  const res = await authenticatedFetch(url, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new ApiRequestError(
      parseApiError(data, `Failed to fetch data (${res.status})`),
      res.status
    );
  }

  return res.json();
};

export async function approveTicket(ticketId: string): Promise<AdminActionResponse> {
  const res = await authenticatedFetch(`${API_BASE}/admin/approve-ticket/${ticketId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiRequestError(
      parseApiError(data, `Failed to approve ticket (${res.status})`),
      res.status
    );
  }

  return data as AdminActionResponse;
}

export async function rejectTicket(ticketId: string): Promise<AdminActionResponse> {
  const res = await authenticatedFetch(`${API_BASE}/admin/reject-ticket/${ticketId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiRequestError(
      parseApiError(data, `Failed to reject ticket (${res.status})`),
      res.status
    );
  }

  return data as AdminActionResponse;
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
