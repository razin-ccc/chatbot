import { API_BASE, authenticatedFetch, readJson } from "@/lib/api/authApi";
import type { Conversation, StoredMessage } from "@/types/conversation";

let createInFlight: Promise<Conversation> | null = null;

export async function listConversations(): Promise<Conversation[]> {
  const response = await authenticatedFetch(`${API_BASE}/conversations`);
  return readJson<Conversation[]>(response, "Failed to load conversations");
}

export async function getConversation(
  conversationId: string
): Promise<Conversation> {
  const response = await authenticatedFetch(
    `${API_BASE}/conversations/${conversationId}`
  );
  return readJson<Conversation>(response, "Conversation not found");
}

export async function getConversationMessages(
  conversationId: string
): Promise<StoredMessage[]> {
  const response = await authenticatedFetch(
    `${API_BASE}/conversations/${conversationId}/messages`
  );
  return readJson<StoredMessage[]>(response, "Failed to load messages");
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
    return readJson<Conversation>(response, "Failed to create conversation");
  })();

  try {
    return await createInFlight;
  } finally {
    createInFlight = null;
  }
}
