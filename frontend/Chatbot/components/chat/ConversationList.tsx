"use client";

import { MessageSquarePlus } from "lucide-react";
import { formatConversationDate } from "@/lib/formatDate";
import { cn } from "@/lib/utils";
import type { Conversation } from "@/types/conversation";

type ConversationListProps = {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  isLoading?: boolean;
  isSwitching?: boolean;
};

export function ConversationList({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  isLoading = false,
  isSwitching = false,
}: ConversationListProps) {
  return (
    <nav
      aria-label="Conversations"
      className="flex h-full min-h-0 flex-col bg-card"
    >
      <div className="flex items-center justify-between gap-2 border-b border-border px-4 py-4">
        <div>
          <h2 className="text-sm font-semibold text-foreground">History</h2>
          <p className="text-xs text-muted-foreground">
            {conversations.length} conversation
            {conversations.length === 1 ? "" : "s"}
          </p>
        </div>
        <button
          type="button"
          onClick={onNewChat}
          disabled={isLoading || isSwitching}
          aria-label="Start new chat"
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl",
            "bg-primary text-primary-foreground transition-colors",
            "hover:bg-primary/90",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            "disabled:cursor-not-allowed disabled:opacity-50"
          )}
        >
          <MessageSquarePlus className="h-5 w-5" aria-hidden />
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <p className="px-3 py-6 text-center text-sm text-muted-foreground">
            Loading conversations…
          </p>
        ) : conversations.length === 0 ? (
          <div className="flex flex-col items-center gap-3 px-3 py-8 text-center">
            <p className="text-sm text-muted-foreground">
              No conversations yet.
            </p>
            <button
              type="button"
              onClick={onNewChat}
              className="rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              Start your first chat
            </button>
          </div>
        ) : (
          <ul role="list" className="space-y-1">
            {conversations.map((item) => {
              const isActive = item.id === activeId;
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => onSelect(item.id)}
                    disabled={isSwitching}
                    aria-current={isActive ? "true" : undefined}
                    className={cn(
                      "flex w-full min-h-11 flex-col gap-0.5 rounded-xl px-3 py-3 text-left transition-colors",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      "disabled:cursor-not-allowed disabled:opacity-50",
                      isActive
                        ? "bg-primary/10 text-foreground ring-1 ring-primary/20"
                        : "text-foreground hover:bg-muted"
                    )}
                  >
                    <span className="line-clamp-1 text-sm font-medium">
                      {item.title ?? "New Conversation"}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {formatConversationDate(item.created_at)}
                    </span>
                    <span
                      className="truncate font-mono text-[10px] text-muted-foreground/80"
                      title={item.id}
                    >
                      {item.id.slice(0, 8)}…
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </nav>
  );
}
