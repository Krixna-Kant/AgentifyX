"""SQLAlchemy models for AgentifyX."""

from sqlalchemy import Column, String, DateTime, Float, Text
from app.db.database import Base


class AnalysisSession(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime)
    document_name = Column(String)
    industry_id = Column(String, nullable=True)
    framework_selected = Column(String, nullable=True)
    composite_readiness = Column(Float)
    roster_json = Column(Text)       # Full AgentRoster as JSON string
    chat_history = Column(Text)      # JSON array of messages
