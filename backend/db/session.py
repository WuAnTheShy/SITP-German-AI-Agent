import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_database_url = (os.getenv("DATABASE_URL", "") or "").strip()
if _database_url:
    DATABASE_URL = _database_url
else:
    db_user = (os.getenv("DB_USER", "postgres") or "postgres").strip()
    db_password = (os.getenv("DB_PASSWORD", "") or "").strip()
    db_host = (os.getenv("DB_HOST", "localhost") or "localhost").strip()
    db_port = (os.getenv("DB_PORT", "5432") or "5432").strip()
    db_name = (os.getenv("DB_NAME", "sitp_german_ai_agent") or "sitp_german_ai_agent").strip()
    auth = f"{db_user}:{db_password}" if db_password else db_user
    DATABASE_URL = f"postgresql+psycopg://{auth}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
