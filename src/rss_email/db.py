import os
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Paper(Base):
    __tablename__ = "papers"

    id = Column(String, primary_key=True)  # fingerprint
    title = Column(String, nullable=False)
    authors = Column(String, default="")
    summary = Column(Text, default="")
    link = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=True)
    source = Column(String, default="")
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now())
    inserted_at = Column(DateTime, default=datetime.now())


def _ensure_sqlite_dir(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    path = database_url.replace("sqlite:///", "", 1)
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def create_session_factory(database_url: str):
    _ensure_sqlite_dir(database_url)
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_paper(session, paper_id: str) -> Optional[Paper]:
    return session.get(Paper, paper_id)
