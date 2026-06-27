"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { logout } from "@/lib/api/authApi";

type UseLogoutOptions = {
  redirectTo?: string;
  onBeforeLogout?: () => void;
};

export function useLogout(options: UseLogoutOptions = {}) {
  const { redirectTo = "/login", onBeforeLogout } = options;
  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = useCallback(async () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    onBeforeLogout?.();
    try {
      await logout();
    } finally {
      router.replace(redirectTo);
    }
  }, [isLoggingOut, onBeforeLogout, redirectTo, router]);

  return { isLoggingOut, handleLogout };
}
