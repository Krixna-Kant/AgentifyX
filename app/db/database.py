"""SQLAlchemy database setup for AgentifyX session persistence."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# Ensure the db directory exists
_db_dir = Path(__file__).parent
_db_dir.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{_db_dir / 'agentifyx.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield a DB session, closing it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
