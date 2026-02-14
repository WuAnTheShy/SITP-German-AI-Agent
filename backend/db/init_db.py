from dotenv import load_dotenv 
import os
load_dotenv()  

from db.base import Base
from db.session import engine

# Import models so SQLAlchemy can discover metadata
from models import entities  # noqa: F401

def create_all_tables() -> None:
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功！")

if __name__ == "__main__":
    create_all_tables()
