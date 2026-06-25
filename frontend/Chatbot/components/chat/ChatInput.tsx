"use client";

import { Loader2, Send, Paperclip, Square } from "lucide-react";
import { useRef } from "react";
import TextareaAutosize from "react-textarea-autosize";
import { cn } from "@/lib/utils";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

export type InputMode = "text" | "voice";

type ChatInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
  onUpload?: (file: File) => void;
  isUploading?: boolean;
  isProcessing?: boolean;
  mode?: InputMode;
  onModeChange?: (mode: InputMode) => void;
  voiceStatus?: string | null;
  isVoiceSupported?: boolean;
  onPlayQuestion?: () => void;
  playQuestionRef?: React.RefObject<HTMLButtonElement | null>;
  onVoiceInputActivate?: () => void;
  isSpeaking?: boolean;
  onStopVoice?: () => void;
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
  mode = "text",
  onModeChange,
  voiceStatus = null,
  isVoiceSupported = false,
  onPlayQuestion,
  playQuestionRef,
  onVoiceInputActivate,
  isSpeaking = false,
  onStopVoice,
}: ChatInputProps) {
  const canSend =
    mode === "text" && value.trim().length > 0 && !disabled && !isProcessing;
  const isBusy = isUploading || isProcessing;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isVoiceMode = mode === "voice";

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (isVoiceMode) return;
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

  const handleModeChange = (nextMode: string) => {
    if (nextMode === "text" || nextMode === "voice") {
      onModeChange?.(nextMode);
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

      {(voiceStatus || isSpeaking) && (
        <div className="mx-auto mb-2 flex max-w-3xl items-center justify-center gap-3 rounded-lg bg-muted px-3 py-2 text-xs font-medium text-foreground">
          <span>{isSpeaking ? "Speaking…" : voiceStatus}</span>
          {isSpeaking && (
            <button
              type="button"
              onClick={onStopVoice}
              className={cn(
                "flex h-7 items-center gap-1.5 rounded-md bg-destructive px-2.5 text-destructive-foreground transition-colors",
                "hover:bg-destructive/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              )}
              aria-label="Stop voice output"
            >
              <Square className="h-3 w-3 fill-current" />
              Stop
            </button>
          )}
        </div>
      )}

      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-border bg-card p-2 shadow-sm">
        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || isBusy || isVoiceMode}
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
          onFocus={isVoiceMode ? onVoiceInputActivate : undefined}
          onClick={isVoiceMode ? onVoiceInputActivate : undefined}
          minRows={1}
          maxRows={6}
          disabled={disabled}
          readOnly={isVoiceMode}
          placeholder={
            isVoiceMode ? "Speak your message…" : placeholder
          }
          className={cn(
            "min-h-[44px] flex-1 resize-none bg-transparent px-2 py-2.5 text-sm outline-none",
            "placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50",
            isVoiceMode && "cursor-pointer",
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

      <div className="mx-auto mt-2 flex max-w-3xl flex-col items-center gap-2">
        <ToggleGroup
          type="single"
          value={mode}
          onValueChange={handleModeChange}
          variant="outline"
          size="sm"
          aria-label="Input mode"
        >
          <ToggleGroupItem value="text" aria-label="Text mode">
            Text
          </ToggleGroupItem>
          <ToggleGroupItem
            value="voice"
            aria-label="Voice mode"
            disabled={!isVoiceSupported}
          >
            Voice
          </ToggleGroupItem>
        </ToggleGroup>

        <p className="text-center text-xs text-muted-foreground">
          {isVoiceMode
            ? "Voice mode · speak in the message box · sends 3 seconds after you stop"
            : "Enter to send · Shift+Enter for new line"}
        </p>

        {!isVoiceSupported && (
          <p className="text-center text-xs text-muted-foreground">
            Voice input requires Chrome. Text mode remains available.
          </p>
        )}
      </div>

      <button
        ref={playQuestionRef}
        type="button"
        onClick={onPlayQuestion}
        className="sr-only"
        aria-hidden="true"
        tabIndex={-1}
      >
        Play question
      </button>
    </div>
  );
}
