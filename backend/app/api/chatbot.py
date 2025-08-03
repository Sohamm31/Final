# backend/app/api/chatbot.py

import uuid
import os
import shutil
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from langchain.memory import ConversationBufferMemory

# --- Database Imports ---
from app.db.database import get_db
from app.db import models, schemas

# --- Auth Imports ---
from .security import get_current_user

# Import the core logic functions
from app.services.chatbot_logic import (
    process_pdf,
    process_youtube,
    get_retriever_for_session,
    get_conversation_chain
)

# --- Setup ---
router = APIRouter()
UPLOAD_DIR = "temp_uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- Helper Functions ---
def cleanup_temp_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Removed temp file: {file_path}")

# --- API Endpoints ---

@router.post("/upload-pdf", response_model=schemas.ProcessResponse)
async def upload_pdf_endpoint(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user) # SECURED
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    session_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{session_id}_{file.filename}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        process_pdf(file_path, session_id)

        # LINK TO USER
        new_session = models.ChatSession(
            id=session_id,
            source_type="pdf",
            source_name=file.filename,
            user_id=current_user.id 
        )
        db.add(new_session)
        db.commit()

        return schemas.ProcessResponse(
            session_id=session_id,
            message=f"Successfully processed '{file.filename}'. Ready to chat.",
            filename=file.filename
        )
    except Exception as e:
        db.rollback()
        logging.error(f"An unexpected error occurred during PDF upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        cleanup_temp_file(file_path)


@router.post("/process-youtube", response_model=schemas.ProcessResponse)
async def process_youtube_endpoint(
    request: schemas.YouTubeUrlRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # SECURED
):
    session_id = str(uuid.uuid4())
    video_url = str(request.url)
    
    try:
        process_youtube(video_url, session_id)

        # LINK TO USER
        new_session = models.ChatSession(
            id=session_id,
            source_type="youtube",
            source_name=video_url,
            user_id=current_user.id
        )
        db.add(new_session)
        db.commit()
        
        return schemas.ProcessResponse(
            session_id=session_id,
            message="Successfully processed YouTube video. Ready to chat."
        )
    except Exception as e:
        db.rollback()
        logging.error(f"An unexpected error occurred during YouTube processing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process YouTube URL: {str(e)}")


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat_endpoint(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # SECURED
):
    session = db.query(models.ChatSession).filter(models.ChatSession.id == request.session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found or you do not have permission to access it.")

    try:
        retriever = get_retriever_for_session(request.session_id)
        past_messages = db.query(models.ChatMessage).filter(models.ChatMessage.session_id == request.session_id).order_by(models.ChatMessage.created_at).all()
        
        memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True, 
            output_key='answer'
        )
        for msg in past_messages:
            memory.chat_memory.add_user_message(msg.user_message)
            memory.chat_memory.add_ai_message(msg.ai_response)
            
        chain = get_conversation_chain(retriever, memory)
        
        result = chain.invoke({"question": request.message})
        ai_response = result["answer"]

        new_message = models.ChatMessage(
            id=str(uuid.uuid4()),
            session_id=request.session_id,
            user_message=request.message,
            ai_response=ai_response
        )
        db.add(new_message)
        db.commit()

        return schemas.ChatResponse(
            session_id=request.session_id,
            response=ai_response
        )
    except Exception as e:
        db.rollback()
        logging.error(f"An unexpected error occurred during chat: {e}")
        raise HTTPException(status_code=500, detail=f"Error during chat: {str(e)}")

# --- HISTORY ENDPOINTS ---

@router.get("/history", response_model=List[schemas.ChatSessionInfo])
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves all chat sessions for the currently logged-in user.
    """
    sessions = db.query(models.ChatSession).filter(models.ChatSession.user_id == current_user.id).order_by(models.ChatSession.created_at.desc()).all()
    return sessions

@router.get("/session/{session_id}", response_model=List[schemas.ChatMessageInfo])
def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves all messages for a specific chat session, ensuring the user owns it.
    """
    session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found or you do not have permission to access it.")
    
    messages = db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session_id).order_by(models.ChatMessage.created_at).all()
    return messages
