from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os
from app.utils.logging_config import logger

# Get database URL from environment variable or use a local SQLite file by default
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./community_hero.db")

# Mask credentials in log output
_log_url = SQLALCHEMY_DATABASE_URL.split("@")[-1] if "@" in SQLALCHEMY_DATABASE_URL else SQLALCHEMY_DATABASE_URL
logger.info(f"Connecting to database at ...@{_log_url}")

# pool_pre_ping=True: verifies connections before use — important for Cloud Run
# which can have idle connections dropped by the Cloud SQL proxy.
# connect_args check_same_thread is SQLite-only and must NOT be set for PostgreSQL.
_is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    **({"connect_args": {"check_same_thread": False}} if _is_sqlite else {}),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    logger.debug("Creating new database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        logger.debug("Closing database session")
        db.close()
