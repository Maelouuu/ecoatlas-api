# ecoatlas_api/migrate_sqlite_to_postgres.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, Species, Occurrence, Source

# Base locale SQLite (celle que tu as déjà remplie avec gbif_importer)
SQLITE_URL = "sqlite:///./ecoatlas.db"

# Base distante Render (External Database URL)
PG_URL = os.getenv("DATABASE_URL")
if not PG_URL:
    raise RuntimeError(
        "Tu dois définir la variable d'environnement DATABASE_URL avec l'External Database URL de Render."
    )

# Render donne souvent une URL en postgres://, SQLAlchemy préfère postgresql://
if PG_URL.startswith("postgres://"):
    PG_URL = PG_URL.replace("postgres://", "postgresql://", 1)

print(f"[INFO] SQLite source = {SQLITE_URL}")
print(f"[INFO] Postgres cible = {PG_URL}")

# Engines
sqlite_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
pg_engine = create_engine(PG_URL, future=True)

SqliteSession = sessionmaker(bind=sqlite_engine, autoflush=False, autocommit=False)
PgSession = sessionmaker(bind=pg_engine, autoflush=False, autocommit=False)

def main():
    # Création des tables dans Postgres si besoin
    print("[STEP] Création des tables dans Postgres…")
    Base.metadata.create_all(pg_engine)

    src = SqliteSession()
    dst = PgSession()

    try:
        # --- SOURCES ---
        print("[STEP] Copie des sources…")
        sources = src.query(Source).all()
        for s in sources:
            dst.merge(
                Source(
                    id=s.id,
                    name=s.name,
                    url=s.url,
                )
            )
        dst.commit()
        print(f"[OK] {len(sources)} sources copiées.")

        # --- SPECIES ---
        print("[STEP] Copie des espèces…")
        species_list = src.query(Species).all()
        for sp in species_list:
            dst.merge(
                Species(
                    id=sp.id,
                    common_name=sp.common_name,
                    scientific_name=sp.scientific_name,
                    life_zone=sp.life_zone,
                    biome=sp.biome,
                    population=sp.population,
                    size_newborn_cm=sp.size_newborn_cm,
                    size_adult_cm=sp.size_adult_cm,
                    weight_newborn_kg=sp.weight_newborn_kg,
                    weight_adult_kg=sp.weight_adult_kg,
                    photo_url=sp.photo_url,
                    photo_key=sp.photo_key,
                )
            )
        dst.commit()
        print(f"[OK] {len(species_list)} espèces copiées.")

        # --- OCCURRENCES ---
        print("[STEP] Copie des occurrences…")
        occs = src.query(Occurrence).all()
        for o in occs:
            dst.merge(
                Occurrence(
                    id=o.id,
                    species_id=o.species_id,
                    lat=o.lat,
                    lng=o.lng,
                    start_year=o.start_year,
                    end_year=o.end_year,
                    source_id=o.source_id,
                )
            )
        dst.commit()
        print(f"[OK] {len(occs)} occurrences copiées.")

        print("🎉 Migration terminée avec succès !")

    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    main()
