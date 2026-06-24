import { MessageSquare } from "lucide-react";

export function EmptyState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center text-muted-foreground">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
        <MessageSquare className="h-7 w-7" />
      </div>
      <div>
        <p className="text-base font-medium text-foreground">
          Start a conversation
        </p>
        <p className="mt-1 max-w-sm text-sm">
          Ask anything — replies stream in real time from Gemini via FastAPI
          backend.
        </p>
      </div>
    </div>
  );
}
