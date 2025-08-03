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

class ChatSessionInfo(BaseModel):
    id: str
    source_name: str
    source_type: str 
    created_at: datetime
    class Config:
        orm_mode = True

class ChatMessageInfo(BaseModel):
    user_message: str
    ai_response: str
    class Config:
        orm_mode = True

# --- ADDED: Session Update Schema ---
class SessionUpdate(BaseModel):
    new_name: str

# --- Community Hub Schemas ---
class AnswerBase(BaseModel):
    body: str

class AnswerCreate(AnswerBase):
    pass

class Answer(AnswerBase):
    id: int
    author: UserOut
    created_at: datetime
    class Config:
        orm_mode = True

class QuestionBase(BaseModel):
    title: str
    body: str

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    author: UserOut
    created_at: datetime
    answers: List[Answer] = []
    class Config:
        orm_mode = True

# --- GitHub Analyzer Schemas ---
class GitHubRepoRequest(BaseModel):
    url: str
