from typing import AsyncGenerator, Awaitable, Callable, Optional, Sequence, TypeVar

from pydantic import BaseModel

from core.logging import logger
from schemas.chat import MessageParam
from services.base import AIPlatform

T = TypeVar("T")


class FallbackLLM(AIPlatform):
    """Try the primary model, and use the fallback when should_fallback(error) is true."""

    def __init__(
        self,
        primary: AIPlatform,
        fallback: AIPlatform,
        should_fallback: Callable[[Exception], bool],
    ):
        super().__init__(primary.system_prompt)
        self._primary = primary
        self._fallback = fallback
        self._should_fallback = should_fallback

    async def _with_fallback(self, call: Callable[[AIPlatform], Awaitable[T]]) -> T:
        try:
            return await call(self._primary)
        except Exception as exc:
            if not self._should_fallback(exc):
                raise
            logger.warning("Primary LLM failed, using fallback: %s", type(exc).__name__)
        return await call(self._fallback)

    async def chat(
        self,
        prompt: str,
        history: Optional[Sequence[MessageParam]] = None,
        context_summary: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        has_output = False
        try:
            async for chunk in self._primary.chat(prompt, history, context_summary):
                has_output = True
                yield chunk
            return
        except Exception as exc:
            # Once the user has seen text, a second model can't continue the same
            # sentence, so a mid-stream failure is reported instead of restarted.
            if has_output or not self._should_fallback(exc):
                raise
            logger.warning("Primary LLM failed, using fallback: %s", type(exc).__name__)

        async for chunk in self._fallback.chat(prompt, history, context_summary):
            yield chunk

    async def classify_json(
        self, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> BaseModel:
        return await self._with_fallback(
            lambda llm: llm.classify_json(system_prompt, user_prompt, schema)
        )

    async def _complete_text(
        self, system_instruction: str, prompt: str, max_output_tokens: int
    ) -> str:
        return await self._with_fallback(
            lambda llm: llm._complete_text(system_instruction, prompt, max_output_tokens)
        )
