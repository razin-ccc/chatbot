import { API_BASE, authenticatedFetch, readJson } from "@/lib/api/authApi";
import type { RagDocument } from "@/types/document";

export async function listDocuments(
  conversationId: string
): Promise<RagDocument[]> {
  const response = await authenticatedFetch(
    `${API_BASE}/conversations/${conversationId}/documents`
  );
  return readJson<RagDocument[]>(response, "Failed to load documents");
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
  return readJson<RagDocument>(response, "Failed to upload document");
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
    // 204 No Content has no body; readJson would still parse fine, but a delete
    // has nothing to return, so only surface an error on failure.
    await readJson<unknown>(response, "Failed to delete document");
  }
}
