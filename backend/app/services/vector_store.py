from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from core.config import getSettings
from pinecone import AsyncPinecone, ServerlessSpec


@dataclass
class VectorChunk:
    id: str
    document_id: UUID
    user_id: UUID
    filename: str
    page: Optional[int]
    chunk_index: int
    content: str
    embedding: list[float]
    parent_id: str
    parent_content: str


@dataclass
class VectorSearchResult:
    document_id: UUID
    filename: str
    page: Optional[int]
    chunk_index: int
    content: str
    score: float
    parent_id: str
    parent_content: str


from fastapi.concurrency import run_in_threadpool


class VectorStoreService(ABC):
    @abstractmethod
    async def add_chunks(self, chunks: list[VectorChunk]) -> None:
        """Adds a list of document chunks to the vector store."""
        pass

    @abstractmethod
    async def query(
        self,
        *,
        user_id: UUID,
        query_embedding: list[float],
        top_k: int,
        document_ids: Optional[list[UUID]] = None,
    ) -> list[VectorSearchResult]:
        """Queries the vector store for similar chunks."""
        pass

    @abstractmethod
    async def delete_document(self, *, user_id: UUID, document_id: UUID) -> None:
        """Deletes all chunks associated with a specific document."""
        pass


class PineconeVectorStoreService(VectorStoreService):
    """
    VectorStoreService backed by Pinecone using the native async SDK.

    Lifecycle:

        1. init(self)      → creates the AsyncPinecone client
        2. initialize()    → must be awaited once to get the async index handle
        3. close()         → must be awaited on shutdown to release the aiohttp pool
    """

    def __init__(self) -> None:
        settings = getSettings()
        self._client = AsyncPinecone(api_key=settings.PINECONE_API)
        self._index_name = settings.PINECONE_INDEX_NAME
        self._index = None

    async def initialize(self) -> None:
        """
        Creates the index if it doesn't exist yet, then gets the
        async index handle for data operations (upsert/query/delete).

        create_index( ) returns an IndexModel (metadata), NOT a data-plane
        handle, so we always need a separate self._client.index() call.
        """
        if not await self._client.has_index(self._index_name):
            await self._client.create_index(
                name=self._index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        self._index = await self._client.index(name=self._index_name)

    async def close(self) -> None:
        """Release the underlying aiohttp connection pool."""
        await self._client.close()

    async def add_chunks(self, chunks: list[VectorChunk]) -> None:
        if not chunks:
            return

        batch_size = 100  # Pinecone recommended batch size
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            vectors = [
                {
                    "id": chunk.id,
                    "values": chunk.embedding,
                    "metadata": {
                        "user_id": str(chunk.user_id),
                        "document_id": str(chunk.document_id),
                        "source": chunk.filename,
                        "page": chunk.page or 0,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "parent_id": chunk.parent_id,
                        "parent_content": chunk.parent_content,
                    },
                }
                for chunk in batch
            ]
            # Native async — runs on the event loop, no threadpool needed
            await self._index.upsert(
                vectors=vectors,
                namespace=str(batch[0].user_id),
            )

    async def query(
        self,
        *,
        user_id: UUID,
        query_embedding: list[float],
        top_k: int,
        document_ids: Optional[list[UUID]] = None,
    ) -> list[VectorSearchResult]:
        if not query_embedding:
            return []

        # Build optional metadata filter for document scoping
        filter_dict: Optional[dict] = None
        if document_ids:
            doc_ids_str = [str(did) for did in document_ids]
            if len(doc_ids_str) == 1:
                filter_dict = {"document_id": {"$eq": doc_ids_str[0]}}
            else:
                filter_dict = {"document_id": {"$in": doc_ids_str}}

        results = await self._index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=str(user_id),
            filter=filter_dict,
            include_metadata=True,
        )

        matches: list[VectorSearchResult] = []
        for match in results.get("matches", []):
            metadata = match["metadata"]
            matches.append(
                VectorSearchResult(
                    document_id=UUID(str(metadata["document_id"])),
                    filename=str(metadata["source"]),
                    page=int(metadata["page"]) if metadata.get("page") else None,
                    chunk_index=int(metadata["chunk_index"]),
                    content=str(metadata["content"]),
                    score=float(match["score"]),  # cosine similarity 0–1
                    parent_id=str(metadata.get("parent_id", "")),
                    parent_content=str(
                        metadata.get("parent_content", metadata["content"])
                    ),
                )
            )
        return matches

    async def delete_document(self, *, user_id: UUID, document_id: UUID) -> None:
        await self._index.delete(
            namespace=str(user_id),
            filter={"document_id": {"$eq": str(document_id)}},
        )
