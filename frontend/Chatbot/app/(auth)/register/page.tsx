"use client";

import { Suspense } from "react";
import AuthForm from "@/components/auth/AuthForm";

export default function RegisterPage() {
  return (
    <Suspense
      fallback={<div className="text-sm text-muted-foreground">Loading…</div>}
    >
      <AuthForm mode="register" />
    </Suspense>
  );
}
