# backend/app/api/github.py

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models, schemas
from app.db.database import get_db
from .security import get_current_user

# Import the new logic for GitHub
from app.services.github_logic import process_github_repo
# Import shared logic from the chatbot service
from app.services.chatbot_logic import get_retriever_for_session, get_conversation_chain
from langchain.memory import ConversationBufferMemory

router = APIRouter()

@router.post("/process-repo", response_model=schemas.ProcessResponse)
async def process_repo_endpoint(
    request: schemas.GitHubRepoRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Processes a GitHub repository URL, creating a new chat session.
    """
    session_id = str(uuid.uuid4())
    repo_url = request.url
    repo_name = repo_url.split('/')[-1] # Simple name extraction

    try:
        # This can be a long-running task, for a production app,
        # you would use a background worker (e.g., Celery).
        process_github_repo(repo_url, session_id)

        # Create a new chat session record linked to the user
        new_session = models.ChatSession(
            id=session_id,
            source_type="github",
            source_name=repo_name,
            user_id=current_user.id
        )
        db.add(new_session)
        db.commit()

        return schemas.ProcessResponse(
            session_id=session_id,
            message=f"Successfully processed repository '{repo_name}'. Ready to chat.",
            filename=repo_name
        )
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to process GitHub repo {repo_url}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process repository: {str(e)}")

# Note: The /chat, /history, and /session/{session_id} endpoints in chatbot.py
# will work for GitHub sessions as well, since they are generic and just use the session_id.
# No need to duplicate them here.
