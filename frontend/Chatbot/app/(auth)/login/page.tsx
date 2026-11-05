"use client";

import { Suspense } from "react";
import AuthForm from "@/components/auth/AuthForm";

export default function LoginPage() {
  return (
    <Suspense
      fallback={<div className="text-sm text-muted-foreground">Loading…</div>}
    >
      <AuthForm mode="login" />
    </Suspense>
  );
}
