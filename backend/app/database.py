"""Database connection and session management with PostgreSQL and SQLite auto-fallback."""
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

logger = logging.getLogger("trustgate.database")

Base = declarative_base()

def get_engine():
    """Initializes SQLAlchemy engine with PostgreSQL or auto-fallback to SQLite."""
    # Attempt PostgreSQL if URL starts with postgres
    if settings.DATABASE_URL.startswith("postgres"):
        try:
            logger.info("Attempting connection to PostgreSQL: %s", settings.DATABASE_URL.split("@")[-1])
            engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                connect_args={"connect_timeout": 3}
            )
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to PostgreSQL database.")
            return engine
        except Exception as e:
            logger.warning(
                "PostgreSQL connection failed (%s). Falling back to SQLite database at %s",
                e,
                settings.SQLITE_FALLBACK_URL
            )

    # Fallback to SQLite
    engine = create_engine(
        settings.SQLITE_FALLBACK_URL,
        connect_args={"check_same_thread": False}
    )
    logger.info("Using SQLite database: %s", settings.SQLITE_FALLBACK_URL)
    return engine

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Creates all database tables."""
    import app.models  # Ensure all models are registered
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
