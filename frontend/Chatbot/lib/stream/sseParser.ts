import type { ChatStreamChunk } from "@/types/chat";

export function parseSSEBuffer(buffer: string): {
  events: ChatStreamChunk[];
  remainder: string;
} {
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() ?? "";
  const events: ChatStreamChunk[] = [];

  for (const part of parts) {
    const line = part
      .split("\n")
      .map((l) => l.trim())
      .find((l) => l.startsWith("data:"));
    if (!line) continue;

    const json = line.slice(5).trim();
    if (!json) continue;

    try {
      events.push(JSON.parse(json) as ChatStreamChunk);
    } catch {
      // ignore malformed chunks
    }
  }

  return { events, remainder };
}
