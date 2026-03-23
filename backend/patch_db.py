import os
from sqlalchemy import create_engine, text

def _build_database_url() -> str:
    direct = (os.getenv("DATABASE_URL", "") or "").strip()
    if direct:
        return direct
    db_user = (os.getenv("DB_USER", "postgres") or "postgres").strip()
    db_password = (os.getenv("DB_PASSWORD", "") or "").strip()
    db_host = (os.getenv("DB_HOST", "localhost") or "localhost").strip()
    db_port = (os.getenv("DB_PORT", "5432") or "5432").strip()
    db_name = (os.getenv("DB_NAME", "sitp_german_ai_agent") or "sitp_german_ai_agent").strip()
    auth = f"{db_user}:{db_password}" if db_password else db_user
    return f"postgresql+psycopg://{auth}@{db_host}:{db_port}/{db_name}"


DATABASE_URL = _build_database_url()

engine = create_engine(DATABASE_URL)

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE exams ADD COLUMN content JSONB DEFAULT '[]'::jsonb NOT NULL;"))
    print("Column added successfully.")
except Exception as e:
    print(f"Error adding column (maybe it already exists?): {e}")
