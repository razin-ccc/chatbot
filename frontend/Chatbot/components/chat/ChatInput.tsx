"use client";

import { Loader2, Send, Paperclip } from "lucide-react";
import { useRef } from "react";
import TextareaAutosize from "react-textarea-autosize";
import { cn } from "@/lib/utils";

type ChatInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
  onUpload?: (file: File) => void;
  isUploading?: boolean;
  isProcessing?: boolean;
};

export function ChatInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder = "Message Gemini…",
  onUpload,
  isUploading = false,
  isProcessing = false,
}: ChatInputProps) {
  const canSend = value.trim().length > 0 && !disabled && !isProcessing;
  const isBusy = isUploading || isProcessing;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSend) onSubmit();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onUpload) {
      onUpload(file);
    }
    if (e.target) {
      e.target.value = "";
    }
  };

  return (
    <div className="border-t border-border bg-background/80 p-4 backdrop-blur-sm">
      {isBusy && (
        <div className="mx-auto mb-2 flex max-w-3xl items-center gap-2 rounded-lg bg-primary/10 px-3 py-2 text-xs font-medium text-primary">
          <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin" />
          <span>
            {isUploading ? "Uploading document..." : "Processing document..."}
          </span>
        </div>
      )}
      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-border bg-card p-2 shadow-sm">
        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || isBusy}
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-xl transition-colors text-muted-foreground",
              "hover:bg-muted hover:text-foreground",
              "disabled:cursor-not-allowed disabled:opacity-40",
            )}
            aria-label="Attach document"
          >
            <Paperclip className="h-5 w-5" />
          </button>
        </div>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          accept=".pdf,.txt,application/pdf,text/plain"
        />
        <TextareaAutosize
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          minRows={1}
          maxRows={6}
          disabled={disabled}
          placeholder={placeholder}
          className={cn(
            "min-h-[44px] flex-1 resize-none bg-transparent px-2 py-2.5 text-sm outline-none",
            "placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50",
          )}
        />
        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSend}
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors",
            "bg-primary text-primary-foreground hover:bg-primary/90",
            "disabled:cursor-not-allowed disabled:opacity-40",
          )}
          aria-label="Send message"
        >
          {(disabled || isBusy) && !canSend ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </div>
      <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-muted-foreground">
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  );
}
