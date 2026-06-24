from fastapi import APIRouter, Request, Depends, Security
from fastapi.responses import StreamingResponse
from schemas.chat import ChatRequest
from core.logging import logger
from sqlalchemy.ext.asyncio import AsyncSession
from auth.service import get_current_active_user
from core.database import get_db
from schemas.models import User
from services.conversation import get_user_conversation
from services.graph.runner import run_graph_stream

chat_router = APIRouter()


@chat_router.post(
    "/chat",
    status_code=200,
    responses={
        200: {
            "content": {
                "text/event-stream": {
                    "example": {
                        "data": [
                            {
                                "success": True,
                                "data": {
                                    "content": "Initial Content",
                                    "finishReason": "Null",
                                },
                            },
                            {
                                "success": True,
                                "data": {
                                    "content": "Content Continue",
                                    "finishReason": "Null",
                                },
                            },
                            {
                                "success": True,
                                "data": {
                                    "content": "",
                                    "finishReason": "STOP",
                                },
                            },
                        ]
                    }
                }
            }
        }
    },
)
async def chat_stream_endpoint(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_current_active_user, scopes=["ai:chat"]),
):
    """Stream a chat response via the LangGraph Intelligent Router."""
    logger.info(f"POST /chat endpoint was hit with {chat_request} request")

    # Ensure conversation belongs to user before starting graph
    await get_user_conversation(db, chat_request.conversation_id, current_user.id)

    return StreamingResponse(
        run_graph_stream(
            request=request,
            chat_request=chat_request,
            current_user=current_user,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
