from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Sequence

import tiktoken
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from schemas.chat import MessageParam

# An approximation: no provider's tokenizer is exactly cl100k_base. The budget in
# context_budget.py keeps a safety margin (SUMMARIZE_THRESHOLD) to absorb the error.
_ENCODING = tiktoken.get_encoding("cl100k_base")

# Mirrored by context_budget.PER_MESSAGE_TOKENS.
_PER_MESSAGE_TOKENS = 4

_SUMMARY_INSTRUCTION = (
    "Merge the conversation history into a concise rolling summary. "
    "Preserve key facts, names, decisions, and user preferences. "
    "Output only the summary text."
)
_SUMMARY_MAX_OUTPUT_TOKENS = 4096


def _count_texts_tokens_sync(texts: list[str]) -> list[int]:
    return [len(_ENCODING.encode(text)) if text else 0 for text in texts]


class AIPlatform(ABC):
    """
    The contract the rest of the app depends on.

    A provider implements chat, classify_json and _complete_text. Token counting,
    system-instruction assembly and summarization are provider-independent.
    """

    def __init__(self, system_prompt: Optional[str] = None):
        self.system_prompt = system_prompt or ""

    @abstractmethod
    def chat(
        self,
        prompt: str,
        history: Optional[Sequence[MessageParam]] = None,
        context_summary: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Yield text fragments of the reply as they are generated."""

    @abstractmethod
    async def classify_json(
        self, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> BaseModel:
        """Return the model's reply validated against schema."""

    @abstractmethod
    async def _complete_text(
        self, system_instruction: str, prompt: str, max_output_tokens: int
    ) -> str:
        """Return a complete, non-streamed reply. May be empty."""

    def _build_system_instruction(self, context_summary: Optional[str] = None) -> str:
        if not context_summary:
            return self.system_prompt
        return (
            f"{self.system_prompt}\n\n"
            "Conversation context so far:\n"
            f"{context_summary}"
        )

    async def count_texts_tokens(self, texts: list[str]) -> list[int]:
        """Token counts for many texts in a single threadpool round-trip."""
        if not texts:
            return []
        return await run_in_threadpool(_count_texts_tokens_sync, texts)

    async def count_messages_tokens(
        self,
        history: Sequence[MessageParam],
        prompt: str = "",
        context_summary: Optional[str] = None,
    ) -> int:
        system_instruction = self._build_system_instruction(context_summary)
        texts = [system_instruction, *(m.content for m in history), prompt]
        counts = await self.count_texts_tokens(texts)
        num_messages = len(history) + (1 if prompt else 0)
        return sum(counts) + num_messages * _PER_MESSAGE_TOKENS

    async def summarize_messages(
        self,
        evicted_messages: list[MessageParam],
        existing_summary: Optional[str] = None,
    ) -> str:
        lines = []
        if existing_summary:
            lines.append(f"Previous summary:\n{existing_summary}\n")
        lines.append("New messages to incorporate into the summary:\n")
        for msg in evicted_messages:
            lines.append(f"{msg.role}: {msg.content}\n")

        summary = await self._complete_text(
            _SUMMARY_INSTRUCTION, "".join(lines), _SUMMARY_MAX_OUTPUT_TOKENS
        )
        return summary or existing_summary or ""
