# backend/app/services/chatbot_logic.py

import os
# Set this environment variable at the very top, before other imports
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from dotenv import load_dotenv
load_dotenv()

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader, YoutubeLoader
from langchain.memory import ConversationBufferMemory
from langchain.schema.retriever import BaseRetriever
from langchain_openai import ChatOpenAI
from youtube_transcript_api import YouTubeTranscriptApi

# --- Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

CHROMA_PERSIST_DIR = "chroma_db_storage"
if not os.path.exists(CHROMA_PERSIST_DIR):
    os.makedirs(CHROMA_PERSIST_DIR)

if not OPENROUTER_API_KEY:
    print("FATAL ERROR: OPENROUTER_API_KEY not found in .env file.")

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

def process_pdf(pdf_file_path: str, session_id: str):
    """
    Processes a PDF file and creates a persistent vector store.
    """
    print(f"Loading PDF: {pdf_file_path}")
    loader = PyPDFLoader(pdf_file_path)
    documents = loader.load()

    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    print(f"Creating and persisting vector store for session: {session_id}")
    persist_directory = os.path.join(CHROMA_PERSIST_DIR, session_id)
    
    Chroma.from_documents(
        documents=texts, 
        embedding=embedding_model,
        persist_directory=persist_directory
    )
    print("Vector store for PDF created successfully.")


def process_youtube(youtube_url: str, session_id: str):
    """
    Processes a YouTube URL and creates a persistent vector store.
    """
    print(f"Loading YouTube transcript from: {youtube_url}")
    try:
        loader = YoutubeLoader.from_youtube_url(youtube_url, add_video_info=False)
        documents = loader.load()
    except Exception as e:
        print(f"Error loading YouTube transcript: {e}")
        if "Could not get transcript" in str(e):
             raise Exception("Could not retrieve transcript for this YouTube video. It might be private, have disabled transcripts, or be a live stream.")
        raise e

    print("Splitting transcript into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    print(f"Creating and persisting vector store for session: {session_id}")
    persist_directory = os.path.join(CHROMA_PERSIST_DIR, session_id)

    Chroma.from_documents(
        documents=texts,
        embedding=embedding_model,
        persist_directory=persist_directory
    )
    print("Vector store for YouTube created successfully.")


def get_retriever_for_session(session_id: str) -> BaseRetriever:
    """
    Loads a persisted vector store from disk and returns a retriever.
    """
    persist_directory = os.path.join(CHROMA_PERSIST_DIR, session_id)
    if not os.path.exists(persist_directory):
        raise FileNotFoundError(f"No data found for session {session_id}")

    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )
    return vectorstore.as_retriever()


def get_conversation_chain(retriever: BaseRetriever, memory):
    """
    Creates a conversational retrieval chain with memory.
    """
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True
    )
    return conversation_chain
