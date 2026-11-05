"use client";

import useSWRInfinite from "swr/infinite";
import { adminFetcher, type CursorPage } from "@/lib/api/adminApi";

type QueryParams = Record<string, string | undefined>;

/** Load a cursor-paginated admin list, skipping any filters left empty. */
export function useCursorPages<T>(url: string, params: QueryParams = {}) {
  const getKey = (index: number, previous: CursorPage<T> | null) => {
    if (previous && !previous.next_cursor) return null;

    const query = new URLSearchParams();
    for (const [name, value] of Object.entries(params)) {
      if (value) query.set(name, value);
    }
    if (previous?.next_cursor) query.set("cursor", previous.next_cursor);

    const queryString = query.toString();
    return queryString ? `${url}?${queryString}` : url;
  };

  const { data, error, isLoading, isValidating, size, setSize, mutate } =
    useSWRInfinite<CursorPage<T>>(getKey, adminFetcher, {
      shouldRetryOnError: false,
      revalidateOnFocus: false,
    });

  return {
    items: data?.flatMap((page) => page.items) ?? [],
    hasMore: Boolean(data?.[data.length - 1]?.next_cursor),
    error,
    isLoading,
    isValidating,
    loadMore: () => setSize(size + 1),
    refresh: mutate,
  };
}
