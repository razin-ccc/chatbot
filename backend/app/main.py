from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import schemas.models  # noqa: F401 - registers ORM models with SQLAlchemy metadata
from api.routes.admin import admin_router
from api.routes.admin_audit import admin_audit_router
from api.routes.admin_users import admin_users_router
from api.routes.conversations import conv_router
from api.routes.documents import documents_router
from api.routes.health import h_router
from api.routes.streamchat import chat_router
from auth.router import auth_router
from core.config import getSettings
from core.errors import (
    UserBaseException,
    application_exception_handler,
    global_exception_handler,
)
from core.lifespan import lifespan
from core.middleware import request_logging_middleware

settings = getSettings()

api_tags = [
    {"name": "Health Check", "description": "App health checks"},
    {"name": "Auth", "description": "User registration and authentication"},
    {"name": "Chat", "description": "Streaming chat endpoints"},
    {"name": "Documents", "description": "Document upload and RAG indexing"},
    {"name": "Admin", "description": "Admin queues and actions"},
]

app = FastAPI(openapi_tags=api_tags, lifespan=lifespan)

app.middleware("http")(request_logging_middleware)
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
