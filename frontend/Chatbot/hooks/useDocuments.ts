"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  deleteDocument,
  listDocuments,
  uploadDocument,
} from "@/lib/api/documentApi";
import type { RagDocument } from "@/types/document";

export function useDocuments(conversationId: string | null) {
  const [documents, setDocuments] = useState<RagDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const hasProcessingDocuments = useMemo(
    () => documents.some((document) => document.status === "processing"),
    [documents]
  );

  const indexedDocumentIds = useMemo(() => {
    const indexed = documents.filter((document) => document.status === "indexed");
    return indexed.length > 0 ? indexed.map((document) => document.id) : undefined;
  }, [documents]);

  const refresh = useCallback(async () => {
    if (!conversationId) {
      setDocuments([]);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      setDocuments(await listDocuments(conversationId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  useEffect(() => {
    const id = window.setTimeout(() => {
      refresh();
    }, 0);

    return () => window.clearTimeout(id);
  }, [refresh]);

  useEffect(() => {
    if (!conversationId || !hasProcessingDocuments) return;

    const id = window.setInterval(() => {
      refresh();
    }, 3000);

    return () => window.clearInterval(id);
  }, [conversationId, hasProcessingDocuments, refresh]);

  const upload = useCallback(
    async (file: File) => {
      if (!conversationId) {
        setError("Select a conversation before uploading documents");
        return;
      }

      setIsUploading(true);
      setError(null);
      try {
        const uploaded = await uploadDocument(conversationId, file);
        setDocuments((prev) => [
          uploaded,
          ...prev.filter((document) => document.id !== uploaded.id),
        ]);
        await refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to upload document");
      } finally {
        setIsUploading(false);
      }
    },
    [conversationId, refresh]
  );

  const remove = useCallback(
    async (id: string) => {
      if (!conversationId) return;

      setDeletingId(id);
      setError(null);
      try {
        await deleteDocument(conversationId, id);
        setDocuments((prev) => prev.filter((document) => document.id !== id));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to delete document");
      } finally {
        setDeletingId(null);
      }
    },
    [conversationId]
  );

  return {
    documents,
    indexedDocumentIds,
    isLoading,
    isUploading,
    deletingId,
    error,
    refresh,
    upload,
    remove,
  };
}
