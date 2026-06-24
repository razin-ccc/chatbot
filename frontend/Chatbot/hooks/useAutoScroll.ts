"use client";

import { useEffect, useRef } from "react";

export function useAutoScroll<T extends HTMLElement>(
  deps: unknown[]
) {
  const bottomRef = useRef<T | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return bottomRef;
}
