# backend/app/db/schemas.py

from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

# --- Authentication Schemas ---

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# --- Chatbot Schemas ---

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str

class YouTubeUrlRequest(BaseModel):
    url: HttpUrl

class ProcessResponse(BaseModel):
    session_id: str
    message: str
    filename: Optional[str] = None

# --- ADDED FOR HISTORY ---
class ChatSessionInfo(BaseModel):
    id: str
    source_name: str
    created_at: datetime

    class Config:
        orm_mode = True

class ChatMessageInfo(BaseModel):
    user_message: str
    ai_response: str

    class Config:
        orm_mode = True
