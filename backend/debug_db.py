import json
import io
from sqlalchemy import select
from db.session import SessionLocal
from models.entities import Homework

def debug():
    db = SessionLocal()
    try:
        stmt = select(Homework).order_by(Homework.created_at.desc()).limit(5)
        hws = db.scalars(stmt).all()
        for hw in hws:
            print(f"ID: {hw.id}, Student: {hw.student_id}, Type: {hw.file_type}, URL (Answers): {hw.file_url[:100]}...")
            if hw.file_type == 'json_exam' and hw.file_url:
                try:
                    data = json.loads(hw.file_url)
                    print(f"  - Parsed JSON keys: {list(data.keys())}")
                except Exception as e:
                    print(f"  - JSON Parse Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug()
