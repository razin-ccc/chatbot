from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.logging import logger
from core.config import getSettings
from api.routes.health import h_router
from api.routes.conversations import conv_router
from api.routes.streamchat import chat_router
from api.routes.documents import documents_router
from api.routes.admin import admin_router
from auth.router import auth_router
from core.errors import (
    UserBaseException,
    application_exception_handler,
    global_exception_handler,
)
from contextlib import asynccontextmanager
from services.gemini import Gemini
from services.memory import RedisMemoryService

import schemas.models  # register ORM models with SQLAlchemy metadata
from services.vector_store import ChromaVectorStoreService, PineconeVectorStoreService
from services.embeddings import EmbeddingService
from services.reranker import RerankerService
from services.graph.graph import graph_builder

settings = getSettings()

api_tags = [
    {"name": "Health Check", "description": "App health checks"},
    {"name": "Auth", "description": "User registration and authentication"},
    {"name": "Chat", "description": "Streaming chat endpoints"},
    {"name": "Documents", "description": "Document upload and RAG indexing"},
    {"name": "Admin", "description": "Admin queues and actions"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_service = None
    reranker_service = None
    pinecone_service = None
    try:
        redis_service = RedisMemoryService()
        await redis_service.redis_client.ping()

        app.state.redis_service = redis_service
        app.state.gemini_service = Gemini(
            api_key=settings.GEMINI_API,
            system_prompt="You are a helpful AI assistant.",
        )
        app.state.embedding_service = EmbeddingService()
        if settings.VECTOR_STORE_PROVIDER == "pinecone":
            pinecone_service = PineconeVectorStoreService()
            await pinecone_service.initialize()
            app.state.vector_store_service = pinecone_service
        else:
            app.state.vector_store_service = ChromaVectorStoreService()
        reranker_service = RerankerService()
        app.state.reranker_service = reranker_service
        app.state.agent_graph = graph_builder()
        logger.info("Successfully initialized and connected to Redis instance!")
    except Exception as e:
        logger.error(f"Failed to initialize services due to ::: {e}")
        raise

    yield

    if pinecone_service is not None:
        await pinecone_service.close()
        logger.info("Application shutting down. Pinecone client closed")

    if reranker_service is not None:
        await reranker_service.close()
        logger.info("Application shutting down. Cohere reranker client closed")
    if redis_service is not None:
        await redis_service.redis_client.aclose()
        logger.info("Application shutting down. Redis connection closed")


app = FastAPI(openapi_tags=api_tags, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(UserBaseException, application_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(h_router, tags=["Health Check"])
app.include_router(auth_router, tags=["Auth"])
app.include_router(conv_router, tags=["Chat"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(documents_router, tags=["Documents"])
app.include_router(admin_router, tags=["Admin"])
