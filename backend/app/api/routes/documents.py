import os
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Request, UploadFile, status, Security
from sqlalchemy.ext.asyncio import AsyncSession

from auth.service import get_current_active_user
from core.database import get_db
from schemas.models import User
from schemas.rag import DocumentResponse
from services.documents import (
    create_document_record,
    delete_conversation_document,
    list_conversation_documents,
    process_document_upload,
    save_uploaded_file_to_temp,
)

documents_router = APIRouter()


@documents_router.post(
    "/conversations/{conversation_id}/documents/upload",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DocumentResponse,
)
async def upload_document(
    request: Request,
    conversation_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_current_active_user, scopes=["documents:create"]),
):
    temp_path: str | None = None
    try:
        temp_path, file_size = await save_uploaded_file_to_temp(file)

        document = await create_document_record(
            db,
            user_id=current_user.id,
            conversation_id=conversation_id,
            filename=file.filename or "document",
            content_type=file.content_type or "application/octet-stream",
            size_bytes=file_size,
        )
        background_tasks.add_task(
            process_document_upload,
            document_id=document.id,
            conversation_id=conversation_id,
            user_id=current_user.id,
            filename=document.filename,
            content_type=document.content_type,
            file_path=temp_path,
            embedding_service=request.app.state.embedding_service,
            vector_store=request.app.state.vector_store_service,
        )
        temp_path = None
        return document
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@documents_router.get(
    "/conversations/{conversation_id}/documents",
    response_model=list[DocumentResponse],
)
async def list_documents(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_current_active_user, scopes=["documents:read"]),
):
    return await list_conversation_documents(db, current_user.id, conversation_id)


@documents_router.delete(
    "/conversations/{conversation_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    request: Request,
    conversation_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_current_active_user, scopes=["documents:delete"]),
):
    await delete_conversation_document(
        db,
        document_id=document_id,
        conversation_id=conversation_id,
        user_id=current_user.id,
        vector_store=request.app.state.vector_store_service,
    )
