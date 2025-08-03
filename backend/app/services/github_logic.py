# backend/app/services/github_logic.py

import os
import shutil
import tempfile
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain_community.document_loaders import GitLoader
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema.retriever import BaseRetriever
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHROMA_PERSIST_DIR = "chroma_db_storage" # We'll store repo DBs here too

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

llm = ChatOpenAI(
    model_name="deepseek/deepseek-r1-0528-qwen3-8b:free",
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.7,
    request_timeout=60
)

def process_github_repo(repo_url: str, session_id: str):
    """
    Clones a GitHub repo, processes its files, and creates a vector store.
    """
    temp_dir = tempfile.mkdtemp(prefix=f"github_clone_{session_id}_")
    print(f"Cloning {repo_url} into {temp_dir}")
    
    try:
        # Clone the repo
        loader = GitLoader(repo_path=temp_dir, clone_url=repo_url, branch="main")
        documents = loader.load()
        print(f"Loaded {len(documents)} documents from {repo_url}")

        # Define language-specific splitters
        python_splitter = RecursiveCharacterTextSplitter.from_language(language=Language.PYTHON, chunk_size=1000, chunk_overlap=200)
        js_splitter = RecursiveCharacterTextSplitter.from_language(language=Language.JS, chunk_size=1000, chunk_overlap=200)
        markdown_splitter = RecursiveCharacterTextSplitter.from_language(language=Language.MARKDOWN, chunk_size=1000, chunk_overlap=200)
        generic_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        processed_docs = []
        for doc in documents:
            file_path = doc.metadata.get('file_path', '')
            file_extension = os.path.splitext(file_path)[1].lower()
            
            chunks = []
            if file_extension == '.py':
                chunks = python_splitter.split_documents([doc])
            elif file_extension in ['.js', '.ts']:
                chunks = js_splitter.split_documents([doc])
            elif file_extension == '.md':
                chunks = markdown_splitter.split_documents([doc])
            # Add other text-based files you want to analyze
            elif file_extension in ['.txt', '.json', '.yml', '.yaml', '.html', '.css']:
                chunks = generic_splitter.split_documents([doc])
            
            processed_docs.extend(chunks)
        
        if not processed_docs:
            raise ValueError("No processable files found in the repository.")

        print(f"Total processed chunks: {len(processed_docs)}")
        
        # Create and persist the vector store
        persist_directory = os.path.join(CHROMA_PERSIST_DIR, session_id)
        Chroma.from_documents(
            documents=processed_docs,
            embedding=embedding_model,
            persist_directory=persist_directory
        )
        print("Vector store for GitHub repo created successfully.")

    finally:
        # Clean up the temporary cloned directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")

# We can reuse the get_retriever and get_conversation_chain from chatbot_logic
# To avoid code duplication, we'll import them in the API file.
