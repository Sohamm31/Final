# backend/app/db/models.py

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    chat_sessions = relationship("ChatSession", back_populates="user")
    questions = relationship("Question", back_populates="author")
    answers = relationship("Answer", back_populates="author")
    interview_sessions = relationship("InterviewSession", back_populates="user")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_type = Column(String(50), nullable=False)
    source_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String(36), primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    session = relationship("ChatSession", back_populates="messages")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    author = relationship("User", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    body = Column(Text, nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    question = relationship("Question", back_populates="answers")
    author = relationship("User", back_populates="answers")

class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # *** FIX: Use server_default for database-side timestamp generation ***
    start_time = Column(DateTime, server_default=func.now(), nullable=False)
    end_time = Column(DateTime, nullable=True)
    resume_text_snippet = Column(Text, nullable=True)
    github_knowledge_summary = Column(Text, nullable=True)

    user = relationship("User", back_populates="interview_sessions")
    conversations = relationship("InterviewConversation", back_populates="session", cascade="all, delete-orphan")
    feedback = relationship("InterviewFeedback", uselist=False, back_populates="session", cascade="all, delete-orphan")

class InterviewConversation(Base):
    __tablename__ = "interview_conversations"
    id = Column(Integer, primary_key=True, index=True)
    interview_session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    # *** FIX: Use server_default for database-side timestamp generation ***
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)

    session = relationship("InterviewSession", back_populates="conversations")

class InterviewFeedback(Base):
    __tablename__ = "interview_feedback"
    id = Column(Integer, primary_key=True, index=True)
    interview_session_id = Column(Integer, ForeignKey("interview_sessions.id"), unique=True, nullable=False)
    technical_rating = Column(Integer, nullable=True)
    technical_tips = Column(Text, nullable=True)
    hr_rating = Column(Integer, nullable=True)
    hr_tips = Column(Text, nullable=True)

    session = relationship("InterviewSession", back_populates="feedback")
