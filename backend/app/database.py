"""Database configuration for SQLModel."""

from sqlmodel import SQLModel, Session, create_engine
from typing import AsyncIterator

# Database URL - using SQLite for local development
DATABASE_URL = "sqlite:///./database.db"

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


def create_db_and_tables() -> None:
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


async def get_session() -> AsyncIterator[Session]:
    """
    Dependency for getting database session.

    Yields:
        Session: Database session
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
