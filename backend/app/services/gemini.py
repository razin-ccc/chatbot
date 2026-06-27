from google import genai
from google.genai import types
from typing import AsyncGenerator, Any, Optional
from schemas.chat import MessageParam
from services.base import AIPlatform
from core.config import getSettings
import tiktoken
from pydantic import BaseModel
from fastapi.concurrency import run_in_threadpool

_ENCODING = tiktoken.get_encoding("cl100k_base")


def _count_texts_tokens_sync(texts: list[str]) -> list[int]:
    return [len(_ENCODING.encode(text)) if text else 0 for text in texts]


def _count_messages_tokens_sync(
    system_instruction: str,
    history_contents: list[str],
    prompt: str,
    num_messages: int,
) -> int:

    total_tokens = 0

    if system_instruction:
        total_tokens += len(_ENCODING.encode(system_instruction))

    for content in history_contents:
        if content:
            total_tokens += len(_ENCODING.encode(content))

    if prompt:
        total_tokens += len(_ENCODING.encode(prompt))

    total_tokens += num_messages * 4
    return total_tokens


class Gemini(AIPlatform):
    MODEL = "gemini-3.1-flash-lite"
    INPUT_TOKEN_LIMIT = 1_048_576
    OUTPUT_TOKEN_LIMIT = 65_536

    def __init__(self, api_key: str, system_prompt: str = None):
        self.system_prompt = system_prompt or ""
        self._client = genai.Client(api_key=api_key)

    def _generation_config(
        self, system_instruction: str, *, max_output_tokens: Optional[int] = None
    ) -> types.GenerateContentConfig:
        settings = getSettings()
        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=max_output_tokens or settings.MODEL_OUTPUT_TOKEN_LIMIT,
        )

    def _build_system_instruction(self, context_summary: Optional[str] = None) -> str:
        if not context_summary:
            return self.system_prompt
        return (
            f"{self.system_prompt}\n\n"
            "Conversation context so far:\n"
            f"{context_summary}"
        )

    def _build_contents(self, history: list[Any], prompt: str) -> list[types.Content]:
        contents: list[types.Content] = []
        if history:
            for msg in history:
                # Handle both Pydantic models (msg.role) and dictionaries (msg["role"])
                role = msg.role if hasattr(msg, "role") else msg.get("role")
                content = msg.content if hasattr(msg, "content") else msg.get("content")
                contents.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=content)])
                )
        contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        )
        return contents

    async def count_texts_tokens(self, texts: list[str]) -> list[int]:
        """Token counts for many texts in a single threadpool round-trip."""
        if not texts:
            return []
        return await run_in_threadpool(_count_texts_tokens_sync, texts)

    async def count_messages_tokens(
        self,
        history: list[Any],
        prompt: str = "",
        context_summary: Optional[str] = None,
    ) -> int:
        system_instruction = self._build_system_instruction(context_summary)
        history_contents = []

        if history:
            for msg in history:
                history_contents.append(
                    msg.content if hasattr(msg, "content") else msg.get("content", "")
                )

        num_messages = len(history) if history else 0
        if prompt:
            num_messages += 1

        return await run_in_threadpool(
            _count_messages_tokens_sync,
            system_instruction,
            history_contents,
            prompt,
            num_messages,
        )

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

        config = self._generation_config(
            system_instruction=(
                "Merge the conversation history into a concise rolling summary. "
                "Preserve key facts, names, decisions, and user preferences. "
                "Output only the summary text."
            ),
            max_output_tokens=4096,
        )
        response = await self._client.aio.models.generate_content(
            model=self.MODEL,
            contents="".join(lines),
            config=config,
        )
        return response.text or existing_summary or ""

    async def chat(
        self,
        prompt: str,
        history: list[Any] = None,
        context_summary: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Yields chunks of text asynchronously for SSE streaming."""
        config = self._generation_config(
            self._build_system_instruction(context_summary),
        )
        contents = self._build_contents(history or [], prompt)
        response = await self._client.aio.models.generate_content_stream(
            model=self.MODEL, contents=contents, config=config
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def classify_json(
        self, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> BaseModel:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema.model_json_schema(),
            temperature=0,
        )
        response = await self._client.aio.models.generate_content(
            model=self.MODEL, contents=user_prompt, config=config
        )
        return schema.model_validate_json(response.text)
