# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# -------------------------------------------------------------------
# Choix de la base de données
# -------------------------------------------------------------------
# En développement : SQLite locale
# En production (Render) : tu définiras la variable d'env DATABASE_URL
# vers une base PostgreSQL (par ex. : postgresql+psycopg2://user:pwd@host/db)
# -------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecoatlas.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    Dépendance FastAPI : fournit une session de DB
    et la ferme automatiquement après la requête.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
