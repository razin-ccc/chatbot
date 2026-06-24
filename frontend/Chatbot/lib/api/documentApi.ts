import { API_BASE, authenticatedFetch, parseApiError } from "@/lib/api/authApi";
import type { RagDocument } from "@/types/document";

export async function listDocuments(
  conversationId: string
): Promise<RagDocument[]> {
  const response = await authenticatedFetch(
    `${API_BASE}/conversations/${conversationId}/documents`
  );
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(parseApiError(data, "Failed to load documents"));
  }

  return data as RagDocument[];
}

export async function uploadDocument(
  conversationId: string,
  file: File
): Promise<RagDocument> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await authenticatedFetch(
    `${API_BASE}/conversations/${conversationId}/documents/upload`,
    {
      method: "POST",
      body: formData,
    }
  );
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(parseApiError(data, "Failed to upload document"));
  }

  return data as RagDocument;
}

export async function deleteDocument(
  conversationId: string,
  id: string
): Promise<void> {
  const response = await authenticatedFetch(
    `${API_BASE}/conversations/${conversationId}/documents/${id}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(parseApiError(data, "Failed to delete document"));
  }
}
