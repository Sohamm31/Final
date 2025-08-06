# backend/app/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# --- Database Configuration ---
# Make sure these details are correct for your MySQL setup.
# Format: "mysql+mysqlconnector://<user>:<password>@<host>[:<port>]/<database>"
DATABASE_URL = "postgresql://engiconnect_pg_db_user:P5QmnaV3ZhYMwANu7C2AsLO9VYSbbyUY@dpg-d29njcqli9vc73fv4qs0-a/engiconnect_pg_db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a SessionLocal class. Each instance of a SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class. Our ORM models will inherit from this class.
Base = declarative_base()

# --- Dependency for FastAPI ---
def get_db():
    """
    A dependency function to get a database session for each request.
    It ensures the database connection is always closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_db_connection():
    """
    Tests the database connection and logs the result.
    This will be called when the application starts up.
    """
    try:
        # The 'connect' method will raise an exception if the connection fails.
        connection = engine.connect()
        connection.close()
        logging.info("Successfully connected to the database.")
        return True
    except Exception as e:
        logging.error(f"Failed to connect to the database. Error: {e}")
        logging.error(f"Please check your DATABASE_URL in database.py and ensure your MySQL server is running.")
        return False
