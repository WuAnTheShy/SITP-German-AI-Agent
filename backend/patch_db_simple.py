import locale
import sys
import os

# 尝试手动更新数据库字段（不依赖 SQLAlchemy）
# 目标：ALTER TABLE exams ADD COLUMN content JSONB DEFAULT '[]'::jsonb NOT NULL;


def _get_pg_conninfo() -> str:
    direct = (os.getenv("DATABASE_URL", "") or "").strip()
    if direct.startswith("postgresql") or direct.startswith("postgres"):
        return direct
    db_host = (os.getenv("DB_HOST", "localhost") or "localhost").strip()
    db_port = (os.getenv("DB_PORT", "5432") or "5432").strip()
    db_name = (os.getenv("DB_NAME", "sitp_german_ai_agent") or "sitp_german_ai_agent").strip()
    db_user = (os.getenv("DB_USER", "postgres") or "postgres").strip()
    db_password = (os.getenv("DB_PASSWORD", "") or "").strip()
    password_part = f" password={db_password}" if db_password else ""
    return f"host={db_host} port={db_port} dbname={db_name} user={db_user}{password_part}"

def run_patch():
    conninfo = _get_pg_conninfo()
    try:
        import psycopg
        print("Using psycopg (v3)...")
        conn = psycopg.connect(conninfo)
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE exams ADD COLUMN IF NOT EXISTS content JSONB DEFAULT '[]'::jsonb NOT NULL;")
            cur.execute("ALTER TABLE exam_assignments ADD COLUMN IF NOT EXISTS personalized_content JSONB;")
            conn.commit()
        print("Success: Column 'content' added to 'exams' table and 'personalized_content' added to 'exam_assignments' table.")
        return True
    except ImportError:
        try:
            import psycopg2
            print("Using psycopg2 (v2)...")
            import psycopg2.extras
            conn = psycopg2.connect(conninfo)
            with conn.cursor() as cur:
                cur.execute("ALTER TABLE exams ADD COLUMN IF NOT EXISTS content JSONB DEFAULT '[]'::jsonb NOT NULL;")
                cur.execute("ALTER TABLE exam_assignments ADD COLUMN IF NOT EXISTS personalized_content JSONB;")
                conn.commit()
            print("Success: Column 'content' added to 'exams' table and 'personalized_content' added to 'exam_assignments' table.")
            return True
        except ImportError:
            print("Error: Neither psycopg nor psycopg2 is installed in this Python environment.")
            return False
    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    run_patch()
