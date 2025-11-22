# ecoatlas_api/migrate_sqlite_to_postgres.py

import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from .models import Base, Species, Occurrence, Source
# Si tu ajoutes d'autres modèles plus tard, tu pourras les importer ici

# SQLite local (déjà rempli par gbif_importer)
SQLITE_URL = "sqlite:///./ecoatlas.db"

# Base distante (External Database URL Render)
PG_URL = os.getenv("DATABASE_URL")
if not PG_URL:
    raise RuntimeError("DATABASE_URL n'est pas défini.")

# Render donne souvent du postgres://, SQLAlchemy préfère postgresql://
if PG_URL.startswith("postgres://"):
    PG_URL = PG_URL.replace("postgres://", "postgresql://", 1)

print("[INFO] SQLite = ", SQLITE_URL)
print("[INFO] Postgres = ", PG_URL)

sqlite_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
pg_engine = create_engine(PG_URL, future=True)

SqliteSession = sessionmaker(bind=sqlite_engine)
PgSession = sessionmaker(bind=pg_engine)


def copy_table(src_session, dst_session, model):
    """Copie générique d'une table SQLAlchemy par introspection."""
    insp = inspect(model)
    columns = [c.key for c in insp.columns]

    rows = src_session.query(model).all()
    print(f"  -> {model.__tablename__}: {len(rows)} lignes")

    for row in rows:
        data = {}
        for col in columns:
            data[col] = getattr(row, col)
        # merge = upsert (insert ou update si déjà présent)
        dst_session.merge(model(**data))

    dst_session.commit()


def main():
    print("[STEP] Création des tables dans Postgres…")
    Base.metadata.create_all(pg_engine)

    src = SqliteSession()
    dst = PgSession()

    try:
        # IMPORTANT : respecter l'ordre des dépendances FK
        print("[STEP] Copie des espèces…")
        copy_table(src, dst, Species)

        print("[STEP] Copie des occurrences…")
        copy_table(src, dst, Occurrence)

        print("[STEP] Copie des sources…")
        copy_table(src, dst, Source)

        print("🎉 Migration terminée avec succès !")

    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    main()
