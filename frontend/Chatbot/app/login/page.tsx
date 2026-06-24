"use client";

import { Suspense } from "react";
import AuthForm from "@/components/Form";

function LoginForm() {
  return <AuthForm mode="login" />;
}

export default function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <Suspense
        fallback={
          <div className="text-sm text-muted-foreground">Loading…</div>
        }
      >
        <LoginForm />
      </Suspense>
    </main>
  );
}
