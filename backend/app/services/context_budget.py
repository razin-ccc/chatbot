from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence
from core.config import getSettings
from schemas.chat import MessageParam
from services.gemini import Gemini


@dataclass
class PreparedContext:
    """
    Result of applying token-budget and truncation rules.

    - messages: recent turns to send as Gemini history
    - summary: updated rolling summary (may be unchanged)
    """

    messages: list[MessageParam]
    summary: Optional[str]


def _pop_oldest_pair(working: list[MessageParam], evicted: list[MessageParam]) -> None:
    """Evict the oldest user/model pair, preserving turn parity."""
    evicted.append(working.pop(0))
    if working:
        evicted.append(working.pop(0))


async def compact_history(
    *,
    gemini: Gemini,
    history: Sequence[MessageParam],
    summary: Optional[str],
    prompt: str = "",
) -> PreparedContext:
    """
    Single eviction path for conversation context.

    Drops oldest turns when either:
    - message count exceeds MAX_REDIS_MESSAGES, or
    - estimated tokens exceed SUMMARIZE_THRESHOLD of the input limit.

    Evicted turns are merged into the rolling summary before removal.
    """
    settings = getSettings()
    working: list[MessageParam] = list(history)
    evicted: list[MessageParam] = []

    min_recent_messages = settings.MIN_RECENT_TURNS * 2
    max_messages = settings.MAX_REDIS_MESSAGES
    buffer = settings.INPUT_TOKEN_BUFFER
    soft_limit = int(settings.MODEL_INPUT_TOKEN_LIMIT * settings.SUMMARIZE_THRESHOLD)

    async def current_usage_tokens() -> int:
        return await gemini.count_messages_tokens(
            history=working,
            prompt=prompt,
            context_summary=summary,
        )

    def over_message_limit() -> bool:
        return len(working) > max_messages

    total_tokens = await current_usage_tokens()
    over_token_limit = total_tokens + buffer > soft_limit

    if not over_message_limit() and not over_token_limit:
        return PreparedContext(messages=working, summary=summary)

    while len(working) > min_recent_messages and over_message_limit():
        _pop_oldest_pair(working, evicted)

    total_tokens = await current_usage_tokens()
    while len(working) > min_recent_messages and total_tokens + buffer > soft_limit:
        _pop_oldest_pair(working, evicted)
        total_tokens -= 150

    if evicted:
        total_tokens = await current_usage_tokens()
        while len(working) > min_recent_messages and (
            over_message_limit() or total_tokens + buffer > soft_limit
        ):
            _pop_oldest_pair(working, evicted)
            total_tokens = await current_usage_tokens()

    new_summary = summary
    if evicted:
        new_summary = await gemini.summarize_messages(
            evicted_messages=evicted,
            existing_summary=summary,
        )

    return PreparedContext(messages=working, summary=new_summary)


async def apply_token_budget(
    *,
    gemini: Gemini,
    history: Sequence[MessageParam],
    prompt: str,
    summary: Optional[str],
) -> PreparedContext:
    """Prepare context for a live request (history + prompt token budget)."""
    return await compact_history(
        gemini=gemini,
        history=history,
        summary=summary,
        prompt=prompt,
    )
