export type ChatRole = "user" | "model";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  status?: "streaming" | "done" | "error";
  sources?: SourceReference[];
};

export type ChatStreamDelta = {
  content: string;
  finishReason?: string | null;
  sources?: SourceReference[] | null;
};

export type ChatStreamSuccess = {
  success: true;
  data: ChatStreamDelta;
};

export type ChatStreamError = {
  success: false;
  error: { code: string; message: string };
};

export type ChatStreamChunk = ChatStreamSuccess | ChatStreamError;

export type SourceReference = {
  documentId: string;
  filename: string;
  page?: number | null;
  chunkIndex: number;
  snippet: string;
  score?: number | null;
};
