from db.base import Base
from db.session import engine

# Import models so SQLAlchemy can discover metadata
from models import entities  # noqa: F401


def create_all_tables() -> None:
    Base.metadata.create_all(bind=engine)
