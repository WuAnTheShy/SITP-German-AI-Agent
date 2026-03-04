import locale
import sys
import os

# 尝试手动更新数据库字段（不依赖 SQLAlchemy）
# 目标：ALTER TABLE exams ADD COLUMN content JSONB DEFAULT '[]'::jsonb NOT NULL;

def run_patch():
    try:
        import psycopg
        print("Using psycopg (v3)...")
        conn = psycopg.connect("host=localhost port=5432 dbname=sitp_german_ai_agent user=postgres password=postgres")
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE exams ADD COLUMN content JSONB DEFAULT '[]'::jsonb NOT NULL;")
            conn.commit()
        print("Success: Column 'content' added to 'exams' table.")
        return True
    except ImportError:
        try:
            import psycopg2
            print("Using psycopg2 (v2)...")
            import psycopg2.extras
            conn = psycopg2.connect("host=localhost port=5432 dbname=sitp_german_ai_agent user=postgres password=postgres")
            with conn.cursor() as cur:
                cur.execute("ALTER TABLE exams ADD COLUMN content JSONB DEFAULT '[]'::jsonb NOT NULL;")
                conn.commit()
            print("Success: Column 'content' added to 'exams' table.")
            return True
        except ImportError:
            print("Error: Neither psycopg nor psycopg2 is installed in this Python environment.")
            return False
    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    run_patch()
