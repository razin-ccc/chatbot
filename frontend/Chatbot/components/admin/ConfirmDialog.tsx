"use client";

import { useState } from "react";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import type { AdminActionResponse } from "@/lib/api/adminApi";

export type PendingAction = {
  title: string;
  description: string;
  confirmLabel: string;
  destructive?: boolean;
  run: () => Promise<AdminActionResponse>;
};

/** Confirms an admin action, runs it, and reports the result. */
export function ConfirmDialog({
  action,
  onClose,
  onDone,
}: {
  action: PendingAction | null;
  onClose: () => void;
  onDone: () => void;
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const confirm = async () => {
    if (!action) return;
    setIsSubmitting(true);
    try {
      const result = await action.run();
      toast.success(result.message);
      onDone();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Action failed.");
    } finally {
      setIsSubmitting(false);
      onClose();
    }
  };

  return (
    <AlertDialog
      open={action !== null}
      onOpenChange={(open) => !open && !isSubmitting && onClose()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{action?.title}</AlertDialogTitle>
          <AlertDialogDescription>{action?.description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isSubmitting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            variant={action?.destructive ? "destructive" : "default"}
            disabled={isSubmitting}
            onClick={(event) => {
              event.preventDefault();
              confirm();
            }}
          >
            {isSubmitting ? "Working…" : action?.confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
