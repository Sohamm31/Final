# backend/app/api/community.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import models, schemas
from app.db.database import get_db
from .security import get_current_user

router = APIRouter()

@router.post("/questions", response_model=schemas.Question)
def create_question(
    question: schemas.QuestionCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new question. User must be logged in.
    """
    new_question = models.Question(
        title=question.title, 
        body=question.body, 
        author_id=current_user.id
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return new_question

@router.get("/questions", response_model=List[schemas.Question])
def get_all_questions(db: Session = Depends(get_db)):
    """
    Get a list of all questions. Does not require login.
    """
    questions = db.query(models.Question).order_by(models.Question.created_at.desc()).all()
    return questions

@router.get("/questions/{question_id}", response_model=schemas.Question)
def get_question(question_id: int, db: Session = Depends(get_db)):
    """
    Get a single question by its ID, along with its answers.
    """
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.post("/questions/{question_id}/answers", response_model=schemas.Answer)
def create_answer_for_question(
    question_id: int,
    answer: schemas.AnswerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Post an answer to a specific question. User must be logged in.
    """
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    new_answer = models.Answer(
        body=answer.body, 
        question_id=question_id, 
        author_id=current_user.id
    )
    db.add(new_answer)
    db.commit()
    db.refresh(new_answer)
    return new_answer

# *** ADDED: DELETE Endpoints ***

@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Delete a question. Only the author of the question can delete it.
    """
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this question")
    
    db.delete(question)
    db.commit()
    return

@router.delete("/answers/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Delete an answer. Only the author of the answer can delete it.
    """
    answer = db.query(models.Answer).filter(models.Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    if answer.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this answer")
        
    db.delete(answer)
    db.commit()
    return
