# backend/app/db/models.py

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    """
    SQLAlchemy model for a user, based on your MIS project.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Relationship to link a user to their chat sessions
    chat_sessions = relationship("ChatSession", back_populates="user")


class ChatSession(Base):
    """
    SQLAlchemy model for a chat session.
    Each session is now linked to a user.
    """
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, index=True) # UUID as a string
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Foreign key to User table
    source_type = Column(String(50), nullable=False) # 'pdf' or 'youtube'
    source_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    SQLAlchemy model for a single chat message within a session.
    """
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, index=True) # UUID for the message
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")
