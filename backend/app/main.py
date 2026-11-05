import logging
from time import perf_counter
from uuid import uuid7

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from core.logging import (
    clear_request_context,
    log_event,
    logger,
    set_request_context,
    stop_logging_listener,
)
from core.config import getSettings
from api.routes.health import h_router
from api.routes.conversations import conv_router
from api.routes.streamchat import chat_router
from api.routes.documents import documents_router
from api.routes.admin import admin_router
from api.routes.admin_audit import admin_audit_router
from api.routes.admin_users import admin_users_router
from core.client_info import client_ip_for_logging, client_user_agent
from services.audit import AuditEntry, AuditLogWriter
from auth.router import auth_router
from core.errors import (
    UserBaseException,
    application_exception_handler,
    global_exception_handler,
)
from contextlib import asynccontextmanager
from services.fallback import FallbackLLM
from services.mistral import MistralProvider, is_transient_error
from services.memory import RedisMemoryService

import schemas.models  # register ORM models with SQLAlchemy metadata
from services.vector_store import PineconeVectorStoreService
from services.embeddings import MistralEmbeddingService
from services.reranker import RerankerService
from services.graph.graph import graph_builder

settings = getSettings()

AUDIT_EXCLUDED_PATHS = {"/health"}

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
    audit_writer = AuditLogWriter()
    try:
        audit_writer.start()
        app.state.audit_writer = audit_writer

        redis_service = RedisMemoryService()
        await redis_service.redis_client.ping()

        app.state.redis_service = redis_service
        system_prompt = "You are a helpful AI assistant."
        app.state.llm_service = FallbackLLM(
            primary=MistralProvider(
                api_key=settings.MISTRAL_API_KEY,
                model=settings.MISTRAL_MODEL,
                system_prompt=system_prompt,
            ),
            fallback=MistralProvider(
                api_key=settings.MISTRAL_API_KEY,
                model=settings.MISTRAL_FALLBACK_MODEL,
                system_prompt=system_prompt,
            ),
            should_fallback=is_transient_error,
        )
        app.state.embedding_service = MistralEmbeddingService(
            api_key=settings.MISTRAL_API_KEY,
            model=settings.MISTRAL_EMBED_MODEL,
        )

        pinecone_service = PineconeVectorStoreService()
        await pinecone_service.initialize()
        app.state.vector_store_service = pinecone_service

        reranker_service = RerankerService()
        app.state.reranker_service = reranker_service

        app.state.agent_graph = graph_builder()
        log_event(
            event="app.lifecycle.startup.succeeded",
            message="Application services initialized",
            redis_connected=True,
            vector_store_initialized=True,
            reranker_initialized=True,
        )
    except Exception:
        logger.exception(
            "Application startup failed",
            extra={"event": "app.lifecycle.startup.failed"},
        )
        raise

    yield

    try:
        await audit_writer.stop()

        if pinecone_service is not None:
            await pinecone_service.close()
            log_event(
                event="app.lifecycle.shutdown.pinecone.succeeded",
                message="Pinecone client closed on shutdown",
            )

        if reranker_service is not None:
            await reranker_service.close()
            log_event(
                event="app.lifecycle.shutdown.reranker.succeeded",
                message="Reranker client closed on shutdown",
            )
        if redis_service is not None:
            await redis_service.redis_client.aclose()
            log_event(
                event="app.lifecycle.shutdown.redis.succeeded",
                message="Redis connection closed on shutdown",
            )
    finally:
        stop_logging_listener()


app = FastAPI(openapi_tags=api_tags, lifespan=lifespan)


def _record_audit_entry(request: Request, status_code: int, duration_ms: float) -> None:
    """Queue an audit row. Query strings and bodies are left out, as they may hold private data."""
    if request.method == "OPTIONS" or request.url.path in AUDIT_EXCLUDED_PATHS:
        return
    writer = getattr(request.app.state, "audit_writer", None)
    if writer is None:
        return
    writer.record(
        AuditEntry(
            user_id=getattr(request.state, "user_id", None),
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=round(duration_ms),
            ip_address=client_ip_for_logging(request),
            user_agent=client_user_agent(request),
            request_id=request.state.request_id[:64],
        )
    )


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid7())
    request.state.request_id = request_id
    set_request_context(request_id=request_id)
    start_time = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((perf_counter() - start_time) * 1000, 2)
        log_event(
            event="http.request.process.failed",
            message="HTTP request failed before response generation",
            level=logging.ERROR,
            method=request.method,
            path=request.url.path,
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
            duration_ms=duration_ms,
        )
        _record_audit_entry(request, 500, duration_ms)
        clear_request_context()
        raise

    duration_ms = round((perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    log_event(
        event="http.request.process.succeeded",
        message="HTTP request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    _record_audit_entry(request, response.status_code, duration_ms)
    clear_request_context()
    return response


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
app.include_router(admin_audit_router, tags=["Admin"])
app.include_router(admin_users_router, tags=["Admin"])
