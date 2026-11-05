"use client";

import useSWR, { useSWRConfig } from "swr";
import { API_BASE } from "@/lib/api/authApi";
import {
  adminFetcher,
  type PendingJiraTicketResponse,
} from "@/lib/api/adminApi";
import { ErrorPanel, LoadingPanel } from "./StatePanels";
import { SUMMARY_KEY } from "./SummaryCards";
import { TicketTable } from "./TicketTable";

export function TicketsTab() {
  const { mutate: mutateGlobal } = useSWRConfig();
  const { data, error, isLoading, mutate } = useSWR<PendingJiraTicketResponse[]>(
    `${API_BASE}/admin/pending-tickets`,
    adminFetcher,
    {
      shouldRetryOnError: false,
      revalidateOnFocus: true,
      dedupingInterval: 5_000,
    }
  );

  if (error) return <ErrorPanel error={error} onRetry={() => mutate()} />;
  if (isLoading) return <LoadingPanel />;

  return (
    <TicketTable
      tickets={data ?? []}
      onMutate={() => {
        mutate();
        mutateGlobal(SUMMARY_KEY);
      }}
    />
  );
}
