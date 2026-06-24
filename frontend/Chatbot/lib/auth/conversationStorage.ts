const ACTIVE_CONVERSATION_KEY = "active_conversation_id";

export function getActiveConversationId(): string | null {
  return localStorage.getItem(ACTIVE_CONVERSATION_KEY);
}

export function setActiveConversationId(conversationId: string): void {
  localStorage.setItem(ACTIVE_CONVERSATION_KEY, conversationId);
}

export function clearActiveConversationId(): void {
  localStorage.removeItem(ACTIVE_CONVERSATION_KEY);
}
