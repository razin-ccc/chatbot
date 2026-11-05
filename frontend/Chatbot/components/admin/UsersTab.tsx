"use client";

import { useState } from "react";
import { useSWRConfig } from "swr";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useCursorPages } from "@/hooks/useCursorPages";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { banUser, unbanUser, type AdminUser } from "@/lib/api/adminApi";
import { API_BASE } from "@/lib/api/authApi";
import { formatConversationDate } from "@/lib/formatDate";
import { ConfirmDialog, type PendingAction } from "./ConfirmDialog";
import { SessionsDialog } from "./SessionsDialog";
import { EmptyPanel, ErrorPanel, LoadingPanel } from "./StatePanels";
import { SUMMARY_KEY } from "./SummaryCards";

export function UsersTab() {
  const { mutate: mutateGlobal } = useSWRConfig();
  const [search, setSearch] = useState("");
  const [sessionsUserId, setSessionsUserId] = useState<string | null>(null);
  const [pending, setPending] = useState<PendingAction | null>(null);
  const debouncedSearch = useDebouncedValue(search);

  const { items, hasMore, error, isLoading, isValidating, loadMore, refresh } =
    useCursorPages<AdminUser>(`${API_BASE}/admin/users`, {
      search: debouncedSearch,
    });

  // Looked up by id so the dialog shows fresh counts after an action.
  const sessionsUser = items.find((user) => user.id === sessionsUserId) ?? null;

  const handleChanged = () => {
    refresh();
    mutateGlobal(SUMMARY_KEY);
  };

  const confirmBan = (user: AdminUser) =>
    setPending({
      title: `Ban ${user.email}?`,
      description:
        "They are signed out on every device right away and can't log in until unbanned. Their data is kept.",
      confirmLabel: "Ban user",
      destructive: true,
      run: () => banUser(user.id),
    });

  const confirmUnban = (user: AdminUser) =>
    setPending({
      title: `Unban ${user.email}?`,
      description: "They will be able to log in again.",
      confirmLabel: "Unban user",
      run: () => unbanUser(user.id),
    });

  return (
    <div className="space-y-4">
      <Input
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Search by email"
        aria-label="Search users by email"
        className="w-full sm:w-72"
      />

      {error ? (
        <ErrorPanel error={error} onRetry={() => refresh()} />
      ) : isLoading ? (
        <LoadingPanel />
      ) : items.length === 0 ? (
        <EmptyPanel>No users found.</EmptyPanel>
      ) : (
        <>
          <div className="rounded-lg border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Sessions</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="max-w-64 truncate font-medium">
                          {user.email}
                        </span>
                        {user.is_self && <Badge variant="outline">You</Badge>}
                        {user.is_admin && (
                          <Badge variant="secondary">Admin</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {user.is_active ? (
                        <Badge variant="outline">Active</Badge>
                      ) : (
                        <Badge variant="destructive">Banned</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {user.active_sessions}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      {formatConversationDate(user.created_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSessionsUserId(user.id)}
                        >
                          Sessions
                        </Button>
                        {!user.is_active ? (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => confirmUnban(user)}
                          >
                            Unban
                          </Button>
                        ) : (
                          !user.is_self &&
                          !user.is_admin && (
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => confirmBan(user)}
                            >
                              Ban
                            </Button>
                          )
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          {hasMore && (
            <div className="flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={loadMore}
                disabled={isValidating}
              >
                Load more
              </Button>
            </div>
          )}
        </>
      )}

      <SessionsDialog
        user={sessionsUser}
        onClose={() => setSessionsUserId(null)}
        onChanged={handleChanged}
      />
      <ConfirmDialog
        action={pending}
        onClose={() => setPending(null)}
        onDone={handleChanged}
      />
    </div>
  );
}
