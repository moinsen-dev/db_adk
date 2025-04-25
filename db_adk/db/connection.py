"""
Database connection management for DB-ADK.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from ..config import get_db_url

# Create engine
engine = create_engine(get_db_url())

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

@contextmanager
def get_db_session():
    """Context manager for database sessions.
    
    Yields:
        sqlalchemy.orm.Session: A database session.
        
    Example:
        >>> with get_db_session() as session:
        ...     results = session.query(Agent).all()
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def init_db():
    """Initialize the database by creating all tables."""
    from .models import Base
    Base.metadata.create_all(engine)
