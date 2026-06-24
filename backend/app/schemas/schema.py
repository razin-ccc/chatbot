from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr

    model_config = {"from_attributes": True}


class UserMeResponse(BaseModel):
    id: UUID
    email: EmailStr
    permissions: list[str]


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=8, description="Must be at least 8 characters"
    )


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default="New Conversation", max_length=100)


class ConversationResponse(BaseModel):
    id: UUID
    title: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PendingJiraTicketResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    title: str
    description: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminActionResponse(BaseModel):
    success: bool
    message: str
    jira_key: Optional[str] = None

