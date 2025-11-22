# ecoatlas_api/database.py
"""
Database engine & session – PRO version
Compatible PostgreSQL (Render) + local SQLite fallback.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

# Render PostgreSQL fix
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

# If no env provided → SQLite local
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./ecoatlas.db"

# Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
)

# ORM session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class
Base = declarative_base()


def get_db():
    """
    Dependency used in routers.
    Yields a clean database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
