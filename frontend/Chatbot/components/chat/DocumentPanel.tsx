"use client";

import { FileText, Loader2, RefreshCw, Trash2, X } from "lucide-react";
import { formatConversationDate } from "@/lib/formatDate";
import { cn } from "@/lib/utils";
import type { RagDocument } from "@/types/document";

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function statusClass(document: RagDocument) {
  if (document.status === "indexed")
    return "text-emerald-600 dark:text-emerald-400";
  if (document.status === "failed") return "text-destructive";
  return "text-amber-600 dark:text-amber-400";
}

type DocumentPanelProps = {
  onClose?: () => void;
  documents: RagDocument[];
  isLoading: boolean;
  deletingId: string | null;
  error: string | null;
  refresh: () => void;
  remove: (id: string) => void;
};

export function DocumentPanel({
  onClose,
  documents,
  isLoading,
  deletingId,
  error,
  refresh,
  remove,
}: DocumentPanelProps) {
  return (
    <div className="flex h-full flex-col bg-card">
      <div className="border-b border-border px-4 py-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Documents</h2>
            <p className="text-xs text-muted-foreground">
              Files attached to this conversation
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={refresh}
              disabled={isLoading}
              aria-label="Refresh documents"
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-border text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-50"
            >
              <RefreshCw
                className={cn("h-4 w-4", isLoading && "animate-spin")}
              />
            </button>
            {onClose ? (
              <button
                type="button"
                onClick={onClose}
                aria-label="Close documents"
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-border text-muted-foreground hover:bg-muted hover:text-foreground xl:hidden"
              >
                <X className="h-4 w-4" />
              </button>
            ) : null}
          </div>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4">
        {error && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-2">
          {documents.length === 0 && !isLoading ? (
            <p className="rounded-lg border border-border px-3 py-4 text-center text-xs text-muted-foreground">
              No documents uploaded yet. Attach files from the chat input.
            </p>
          ) : null}

          {documents.map((document) => (
            <div
              key={document.id}
              className="rounded-lg border border-border bg-background p-3"
            >
              <div className="flex min-w-0 items-start justify-between gap-2">
                <div className="flex min-w-0 gap-2">
                  <FileText className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-foreground">
                      {document.filename}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatBytes(document.size_bytes)} |{" "}
                      {formatConversationDate(document.created_at)}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => remove(document.id)}
                  disabled={deletingId === document.id}
                  aria-label={`Delete ${document.filename}`}
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-destructive disabled:opacity-50"
                >
                  {deletingId === document.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </button>
              </div>
              <div className="mt-2 flex items-center justify-between gap-2 text-xs">
                <span
                  className={cn(
                    "font-medium capitalize",
                    statusClass(document),
                  )}
                >
                  {document.status}
                </span>
                <span className="text-muted-foreground">
                  {document.chunkCount} chunks
                </span>
              </div>
              {document.errorMessage ? (
                <p className="mt-2 text-xs text-destructive">
                  {document.errorMessage}
                </p>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
