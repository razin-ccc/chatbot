"use client";

import { useState } from "react";
import useSWR from "swr";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  adminFetcher,
  revokeSession,
  revokeUserSessions,
  type AdminSession,
  type AdminUser,
} from "@/lib/api/adminApi";
import { API_BASE } from "@/lib/api/authApi";
import { formatDateTime } from "@/lib/formatDate";
import { ConfirmDialog, type PendingAction } from "./ConfirmDialog";
import { EmptyPanel, ErrorPanel, LoadingPanel } from "./StatePanels";

export function SessionsDialog({
  user,
  onClose,
  onChanged,
}: {
  user: AdminUser | null;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [pending, setPending] = useState<PendingAction | null>(null);
  const { data, error, isLoading, mutate } = useSWR<AdminSession[]>(
    user ? `${API_BASE}/admin/users/${user.id}/sessions` : null,
    adminFetcher,
    { shouldRetryOnError: false }
  );

  const sessions = data ?? [];

  return (
    <>
      <Dialog
        open={user !== null && pending === null}
        onOpenChange={(open) => !open && onClose()}
      >
        <DialogContent className="flex max-h-[85vh] flex-col sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Active sessions</DialogTitle>
            <DialogDescription className="truncate">
              {user?.email}
            </DialogDescription>
          </DialogHeader>

          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto">
            {error ? (
              <ErrorPanel error={error} onRetry={() => mutate()} />
            ) : isLoading ? (
              <LoadingPanel rows={2} />
            ) : sessions.length === 0 ? (
              <EmptyPanel>This user has no active sessions.</EmptyPanel>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.id}
                  className="flex items-start justify-between gap-4 rounded-lg border p-3"
                >
                  <div className="min-w-0 space-y-1 text-sm">
                    <p className="flex flex-wrap items-center gap-2 font-medium">
                      <span className="font-mono text-xs">
                        {session.ip_address ?? "Unknown IP"}
                      </span>
                      {session.is_current && (
                        <Badge variant="secondary">Your session</Badge>
                      )}
                    </p>
                    <p
                      className="truncate text-xs text-muted-foreground"
                      title={session.user_agent ?? undefined}
                    >
                      {session.user_agent ?? "Unknown device"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Signed in {formatDateTime(session.created_at)}
                      {session.last_rotated_at &&
                        ` · Last refreshed ${formatDateTime(session.last_rotated_at)}`}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={session.is_current}
                    onClick={() =>
                      setPending({
                        title: "Revoke this session?",
                        description:
                          "This device is signed out on its next request.",
                        confirmLabel: "Revoke",
                        destructive: true,
                        run: () => revokeSession(session.id),
                      })
                    }
                  >
                    Revoke
                  </Button>
                </div>
              ))
            )}
          </div>

          {user && !user.is_self && sessions.length > 0 && (
            <div className="flex justify-end">
              <Button
                variant="destructive"
                size="sm"
                onClick={() =>
                  setPending({
                    title: "Revoke all sessions?",
                    description: `${user.email} is signed out on every device, but can log in again.`,
                    confirmLabel: "Revoke all",
                    destructive: true,
                    run: () => revokeUserSessions(user.id),
                  })
                }
              >
                Revoke all sessions
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        action={pending}
        onClose={() => setPending(null)}
        onDone={() => {
          mutate();
          onChanged();
        }}
      />
    </>
  );
}
