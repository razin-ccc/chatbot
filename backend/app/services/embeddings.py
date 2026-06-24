from langchain_huggingface import HuggingFaceEmbeddings
from fastapi.concurrency import run_in_threadpool
from core.config import getSettings


class EmbeddingService:
    def __init__(self):
        settings = getSettings()
        model_kwargs = {
            "backend": "onnx",
            "model_kwargs": {
                "provider": "CPUExecutionProvider",  # Fallback to CPU, ORT is very fast on CPU
            },
        }
        self._model = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs=model_kwargs,
            encode_kwargs={"normalize_embeddings": True},
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # Run CPU-intensive embedding generation in a threadpool
        # to avoid blocking the FastAPI event loop.
        return await run_in_threadpool(self._model.embed_documents, texts)

    async def embed_query(self, text: str) -> list[float]:
        if not text:
            return []
        return await run_in_threadpool(self._model.embed_query, text)
