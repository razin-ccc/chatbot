from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None


class TokenData(BaseModel):
    email: EmailStr | None = None


class RefreshRequest(BaseModel):
    refresh_token: str | None = None
