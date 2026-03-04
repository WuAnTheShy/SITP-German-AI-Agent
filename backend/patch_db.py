import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/sitp_german_ai_agent",
)

engine = create_engine(DATABASE_URL)

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE exams ADD COLUMN content JSONB DEFAULT '[]'::jsonb NOT NULL;"))
    print("Column added successfully.")
except Exception as e:
    print(f"Error adding column (maybe it already exists?): {e}")
