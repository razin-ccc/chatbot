"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import useSWR from "swr";
import { API_BASE } from "@/lib/api/authApi";
import { logout } from "@/lib/api/authApi";
import {
  adminFetcher,
  getAdminErrorMessage,
  type PendingJiraTicketResponse,
} from "@/lib/api/adminApi";
import { TicketTable } from "@/components/admin/TicketTable";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

export default function AdminDashboardPage() {
  const { isAuthenticated } = useAuth({
    redirectTo: "/login?redirect=/admin",
    requiredPermission: "ticket:manage",
    permissionDeniedRedirect: "/chat",
  });

  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try {
      await logout();
    } finally {
      router.replace("/login");
    }
  };

  const { data, error, isLoading, mutate } = useSWR<PendingJiraTicketResponse[]>(
    isAuthenticated ? `${API_BASE}/admin/pending-tickets` : null,
    adminFetcher,
    {
      shouldRetryOnError: false,
      revalidateOnFocus: true,
      dedupingInterval: 5_000,
    }
  );

  if (isAuthenticated === null) {
    return (
      <div className="container mx-auto py-10 px-4 max-w-5xl">
        <div className="p-12 border rounded-md bg-muted/20 text-center animate-pulse">
          Checking session…
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="container mx-auto py-10 px-4 max-w-5xl">
      <div className="flex items-start justify-between gap-4 mb-8">
        <div className="flex flex-col">
          <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Review and manage pending Jira bug reports submitted by users.
          </p>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          disabled={isLoggingOut}
          aria-label="Log out"
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-border",
            "text-muted-foreground transition-colors",
            "hover:bg-muted hover:text-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          <LogOut className="h-5 w-5" aria-hidden />
        </button>
      </div>

      {error ? (
        <div className="p-6 border rounded-md bg-destructive/10 text-destructive text-center">
          {getAdminErrorMessage(error)}
        </div>
      ) : isLoading ? (
        <div className="p-12 border rounded-md bg-muted/20 text-center animate-pulse">
          Loading tickets...
        </div>
      ) : (
        <TicketTable tickets={data || []} onMutate={mutate} />
      )}
    </div>
  );
}
