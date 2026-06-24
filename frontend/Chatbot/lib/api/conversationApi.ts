import {
  API_BASE,
  authenticatedFetch,
  parseApiError,
} from "@/lib/api/authApi";
import type { Conversation, StoredMessage } from "@/types/conversation";

let createInFlight: Promise<Conversation> | null = null;

export async function listConversations(): Promise<Conversation[]> {
  const response = await authenticatedFetch(`${API_BASE}/conversations`);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(parseApiError(data, "Failed to load conversations"));
  }
  return response.json() as Promise<Conversation[]>;
}

export async function getConversation(
  conversationId: string
): Promise<Conversation> {
  const response = await authenticatedFetch(
    `${API_BASE}/conversations/${conversationId}`
  );
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(parseApiError(data, "Conversation not found"));
  }
  return response.json() as Promise<Conversation>;
}

export async function getConversationMessages(
  conversationId: string
): Promise<StoredMessage[]> {
  const response = await authenticatedFetch(
    `${API_BASE}/conversations/${conversationId}/messages`
  );
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(parseApiError(data, "Failed to load messages"));
  }
  return response.json() as Promise<StoredMessage[]>;
}

export async function createConversation(
  title = "New Conversation"
): Promise<Conversation> {
  if (createInFlight) {
    return createInFlight;
  }

  createInFlight = (async () => {
    const response = await authenticatedFetch(`${API_BASE}/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(parseApiError(data, "Failed to create conversation"));
    }

    return data as Conversation;
  })();

  try {
    return await createInFlight;
  } finally {
    createInFlight = null;
  }
}
