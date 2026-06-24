export type DocumentStatus = "processing" | "indexed" | "failed";

export type RagDocument = {
  id: string;
  conversationId: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  status: DocumentStatus;
  chunkCount: number;
  errorMessage?: string | null;
  created_at: string;
  updated_at: string;
};
