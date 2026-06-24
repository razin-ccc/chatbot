from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Any


class AIPlatform(ABC):
    @abstractmethod
    async def chat(
        self, prompt: str, history: Optional[list[Any]] = None
    ) -> AsyncGenerator[str, None]:

        pass
