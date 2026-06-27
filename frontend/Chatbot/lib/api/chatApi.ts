import {
  API_BASE,
  ApiRequestError,
  authenticatedFetch,
  parseApiError,
} from "@/lib/api/authApi";
import { parseSSEBuffer } from "@/lib/stream/sseParser";
import type { ChatStreamSuccess } from "@/types/chat";

export type StreamChatParams = {
  message: string;
  conversationId: string;
  signal?: AbortSignal;
  onChunk: (chunk: ChatStreamSuccess) => void;
};

export async function streamChat({
  message,
  conversationId,
  signal,
  onChunk,
}: StreamChatParams): Promise<void> {
  const response = await authenticatedFetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversationId }),
    signal,
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiRequestError(
      parseApiError(data, `Request failed (${response.status})`),
      response.status
    );
  }

  if (!response.body) {
    throw new Error("No response body from chat stream");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const { events, remainder } = parseSSEBuffer(buffer);
    buffer = remainder;

    for (const event of events) {
      if (!event.success) {
        throw new Error(event.error.message);
      }
      onChunk(event);
    }
  }

  if (buffer.trim()) {
    const { events } = parseSSEBuffer(`${buffer}\n\n`);
    for (const event of events) {
      if (!event.success) {
        throw new Error(event.error.message);
      }
      onChunk(event);
    }
  }
}
