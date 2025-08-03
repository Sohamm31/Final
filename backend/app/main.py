# backend/app/main.py

import uvicorn
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# --- Database Imports ---
from app.db import models
from app.db.database import engine, test_db_connection

# --- API Router Imports ---
from app.api import chatbot, auth, community, github

# Configure logging
logging.basicConfig(level=logging.INFO)

# 1. Initialize the FastAPI App
app = FastAPI(
    title="EngiConnect API",
    description="Backend services for the EngiConnect platform.",
    version="0.1.0"
)

# Mount Static Files
static_files_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_files_path), name="static")


@app.on_event("startup")
def on_startup():
    logging.info("Application starting up...")
    if test_db_connection():
        logging.info("Creating database tables if they don't exist...")
        models.Base.metadata.create_all(bind=engine)
        logging.info("Database tables check/creation complete.")
    else:
        logging.error("FATAL: Could not establish database connection.")

# 2. Configure CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    # *** FIX: Explicitly list all allowed methods to solve the 405 error. ***
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 3. Include API Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["Chatbot"])
app.include_router(community.router, prefix="/api/v1/community", tags=["Community"])
app.include_router(github.router, prefix="/api/v1/github", tags=["GitHub Analyzer"])


# 4. Frontend Serving Endpoints
@app.get("/", include_in_schema=False)
async def serve_landing_page():
    return FileResponse(os.path.join(static_files_path, "index.html"))

@app.get("/chatbot", include_in_schema=False)
async def serve_chatbot_page():
    return FileResponse(os.path.join(static_files_path, "chatbot.html"))

@app.get("/login", include_in_schema=False)
async def serve_login_page():
    return FileResponse(os.path.join(static_files_path, "login.html"))

@app.get("/community", include_in_schema=False)
async def serve_community_page():
    return FileResponse(os.path.join(static_files_path, "community.html"))

@app.get("/github-analyzer", include_in_schema=False)
async def serve_github_page():
    # We will reuse the chatbot.html frontend for this feature
    return FileResponse(os.path.join(static_files_path, "chatbot.html"))


# 5. Running the Application
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
