"use client";

import { Suspense } from "react";
import AuthForm from "@/components/Form";

function RegisterForm() {
  return <AuthForm mode="register" />;
}

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <Suspense
        fallback={
          <div className="text-sm text-muted-foreground">Loading…</div>
        }
      >
        <RegisterForm />
      </Suspense>
    </main>
  );
}
