# backend/app/api/interview.py

import os
import shutil
import tempfile
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import models, schemas
from app.db.database import get_db
from .security import get_current_user
from app.services.interview_logic import process_resume_and_embed, generate_question, get_feedback, determine_next_question_type

router = APIRouter()

# In-memory storage for active interview sessions
active_sessions = {}

@router.post("/upload_resume")
async def upload_resume_endpoint(
    resume_file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_id = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, resume_file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(resume_file.file, buffer)
        
        resume_text, github_knowledge, chroma_db_path = await process_resume_and_embed(file_path, resume_file.filename, session_id)

    # *** FIX: Explicitly set start_time in the code to avoid database errors ***
    new_session = models.InterviewSession(
        user_id=current_user.id,
        start_time=datetime.now(), # This is the main fix
        resume_text_snippet=resume_text[:500],
        github_knowledge_summary=json.dumps(github_knowledge)
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    active_sessions[session_id] = {
        "db_session_id": new_session.id,
        "chroma_db_path": chroma_db_path,
        "conversation_history": [],
        "sections_covered": {'introduction': False, 'skills': False, 'projects': False, 'experience': False},
        "section_questions_asked": {'introduction': 0, 'skills': 0, 'projects': 0, 'experience': 0},
        "max_questions_per_section": 2
    }
    
    return {"message": "Resume processed.", "interview_session_id": session_id}

@router.post("/start_interview")
async def start_interview_endpoint(
    interview_session_id: str = Form(...),
    current_user: models.User = Depends(get_current_user)
):
    session_data = active_sessions.get(interview_session_id)
    if not session_data or not interview_session_id.startswith(f"{current_user.id}_"):
        raise HTTPException(status_code=404, detail="Active interview session not found or unauthorized.")
    
    initial_question = await generate_question(session_data, 'introduction')
    return {"question": initial_question}

@router.post("/submit_answer")
async def submit_answer_endpoint(
    interview_session_id: str = Form(...),
    user_answer: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_data = active_sessions.get(interview_session_id)
    if not session_data or not interview_session_id.startswith(f"{current_user.id}_"):
        raise HTTPException(status_code=404, detail="Active interview session not found or unauthorized.")

    session_data['conversation_history'].append(('user', user_answer))
    
    db_conv = models.InterviewConversation(
        interview_session_id=session_data["db_session_id"], 
        role='user', 
        text=user_answer,
        timestamp=datetime.now() # Explicitly set timestamp
    )
    db.add(db_conv)
    db.commit()

    next_question_type = determine_next_question_type(session_data)
    if next_question_type == 'feedback_stage':
        return {"status": "interview_finished"}

    next_question = await generate_question(session_data, next_question_type, user_answer)
    
    db_conv_ai = models.InterviewConversation(
        interview_session_id=session_data["db_session_id"], 
        role='ai', 
        text=next_question,
        timestamp=datetime.now() # Explicitly set timestamp
    )
    db.add(db_conv_ai)
    db.commit()
    
    return {"question": next_question}

@router.post("/get_feedback")
async def get_feedback_endpoint(
    interview_session_id: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_data = active_sessions.get(interview_session_id)
    if not session_data or not interview_session_id.startswith(f"{current_user.id}_"):
        raise HTTPException(status_code=404, detail="Active interview session not found or unauthorized.")

    technical_feedback, hr_feedback = await get_feedback(session_data)
    
    db_feedback = models.InterviewFeedback(
        interview_session_id=session_data["db_session_id"],
        technical_rating=technical_feedback.technical_knowledge_rating,
        technical_tips=json.dumps(technical_feedback.technical_tips),
        hr_rating=hr_feedback.communication_skills_rating,
        hr_tips=json.dumps(hr_feedback.communication_tips)
    )
    db.add(db_feedback)
    
    db_session = db.query(models.InterviewSession).filter(models.InterviewSession.id == session_data["db_session_id"]).first()
    if db_session:
        db_session.end_time = datetime.now()
    db.commit()

    # Cleanup
    if os.path.exists(session_data['chroma_db_path']):
        shutil.rmtree(session_data['chroma_db_path'])
    del active_sessions[interview_session_id]

    return {
        "technical_feedback": technical_feedback.dict(),
        "hr_feedback": hr_feedback.dict()
    }

@router.get("/history")
async def get_history(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = db.query(models.InterviewSession).filter(models.InterviewSession.user_id == current_user.id).order_by(models.InterviewSession.start_time.desc()).all()
    response = []
    for session in history:
        feedback = session.feedback
        response.append({
            "start_time": session.start_time.isoformat(),
            "resume_snippet": session.resume_text_snippet,
            "github_summary": json.loads(session.github_knowledge_summary) if session.github_knowledge_summary else [],
            "conversation": [{"role": c.role, "text": c.text} for c in session.conversations],
            "technical_feedback": {
                "rating": feedback.technical_rating,
                "tips": json.loads(feedback.technical_tips)
            } if feedback else None,
            "hr_feedback": {
                "rating": feedback.hr_rating,
                "tips": json.loads(feedback.hr_tips)
            } if feedback else None
        })
    return response
