from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os
from app.utils.logging_config import logger

# Get database URL from environment variable or use a local SQLite file by default.
# Strip whitespace/newlines — GCP Secret Manager sometimes injects trailing newlines.
_raw_url = os.getenv("DATABASE_URL", "").strip()

if not _raw_url:
    logger.warning(
        "DATABASE_URL is not set or is empty. Falling back to local SQLite. "
        "This is expected for local dev but NOT for production."
    )
    SQLALCHEMY_DATABASE_URL = "sqlite:///./community_hero.db"
else:
    SQLALCHEMY_DATABASE_URL = _raw_url

# Mask credentials in log output
_log_url = (
    SQLALCHEMY_DATABASE_URL.split("@")[-1]
    if "@" in SQLALCHEMY_DATABASE_URL
    else SQLALCHEMY_DATABASE_URL
)
logger.info(f"Connecting to database at: ...@{_log_url}")

# pool_pre_ping=True: verifies connections before use — important for Cloud Run
# which can have idle connections dropped by the Cloud SQL proxy.
# connect_args check_same_thread is SQLite-only and must NOT be set for PostgreSQL.
# timeout=30 prevents immediate "database is locked" exceptions under concurrent access.
_is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        **({"connect_args": {"check_same_thread": False, "timeout": 30}} if _is_sqlite else {}),
    )
    logger.info("SQLAlchemy engine created successfully.")
except Exception as e:
    logger.error(
        f"Failed to create SQLAlchemy engine. "
        f"Check that DATABASE_URL is a valid connection string "
        f"(e.g. postgresql+psycopg2://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE). "
        f"Error: {e}"
    )
    raise RuntimeError(
        f"Invalid DATABASE_URL. Could not create database engine. "
        f"Raw value hint: '{SQLALCHEMY_DATABASE_URL[:40]}...'. "
        f"Original error: {e}"
    ) from e

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
