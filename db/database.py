import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Base

def _get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        try:
            import streamlit as st
            url = st.secrets.get("DATABASE_URL", "")
        except Exception:
            pass
    return url or "sqlite:///golf_scores.db"

_raw_url = _get_db_url()

# Supabase/Railway give postgres:// but SQLAlchemy needs postgresql://
DB_URL = _raw_url.replace("postgres://", "postgresql://", 1)

_is_sqlite = DB_URL.startswith("sqlite")

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)

    # SQLite-only: patch columns added after initial schema
    if _is_sqlite:
        with engine.connect() as conn:
            for col, definition in [
                ("password_hash", "TEXT"),
                ("avatar_url",    "TEXT"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {definition}"))
                    conn.commit()
                except Exception:
                    pass


def get_session():
    return SessionLocal()
