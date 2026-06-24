"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  fetchCurrentUser,
  subscribeAuthChanges,
  type UserMe,
} from "@/lib/api/authApi";

export type UseAuthOptions = {
  redirectTo?: string;
  requiredPermission?: string;
  permissionDeniedRedirect?: string;
};

export function useAuth(options: string | UseAuthOptions = "/login") {
  const router = useRouter();
  const resolvedOptions =
    typeof options === "string" ? { redirectTo: options } : options;
  const {
    redirectTo = "/login",
    requiredPermission,
    permissionDeniedRedirect = "/chat",
  } = resolvedOptions;

  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [user, setUser] = useState<UserMe | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function verifySession() {
      try {
        const me = await fetchCurrentUser();
        if (cancelled) return;

        if (
          requiredPermission &&
          !me.permissions.includes(requiredPermission)
        ) {
          setUser(null);
          setIsAuthenticated(false);
          router.replace(permissionDeniedRedirect);
          return;
        }

        setUser(me);
        setIsAuthenticated(true);
      } catch {
        if (cancelled) return;
        setUser(null);
        setIsAuthenticated(false);
        router.replace(redirectTo);
      }
    }

    verifySession();

    const unsubscribe = subscribeAuthChanges(() => {
      verifySession();
    });

    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, [
    router,
    redirectTo,
    requiredPermission,
    permissionDeniedRedirect,
  ]);

  return { isAuthenticated, user };
}
