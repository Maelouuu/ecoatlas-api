# ecoatlas_api/crud.py
"""
CRUD layer – PRO VERSION
Optimisé pour PostgreSQL & FastAPI.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, or_

from . import models


# ---------------------------------------------------------
# SPECIES – LIST
# ---------------------------------------------------------

def get_species_list(
    db: Session,
    year: int | None = None,
    life_zone: str | None = None,
    biome: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    query = db.query(models.Species)

    # Filtre année => seulement les espèces avec au moins UNE occurrence active
    if year is not None:
        query = query.filter(
            models.Species.occurrences.any(
                and_(
                    models.Occurrence.start_year <= year,
                    models.Occurrence.end_year >= year,
                )
            )
        )

    if life_zone:
        query = query.filter(models.Species.life_zone.ilike(f"%{life_zone}%"))

    if biome:
        query = query.filter(models.Species.biome.ilike(f"%{biome}%"))

    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            or_(
                models.Species.common_name.ilike(s),
                models.Species.scientific_name.ilike(s),
            )
        )

    return (
        query.order_by(models.Species.common_name.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )


# ---------------------------------------------------------
# SPECIES – SINGLE
# ---------------------------------------------------------

def get_species_by_id(db: Session, species_id: int):
    return (
        db.query(models.Species)
        .options(joinedload(models.Species.occurrences))
        .filter(models.Species.id == species_id)
        .first()
    )


# ---------------------------------------------------------
# OCCURRENCES
# ---------------------------------------------------------

def get_occurrences_for_species(
    db: Session,
    species_id: int,
    from_year: int | None = None,
    to_year: int | None = None,
    source: str | None = None,
):
    q = db.query(models.Occurrence).filter(
        models.Occurrence.species_id == species_id
    )

    if from_year is not None:
        q = q.filter(models.Occurrence.end_year >= from_year)

    if to_year is not None:
        q = q.filter(models.Occurrence.start_year <= to_year)

    if source:
        q = q.filter(models.Occurrence.source == source)

    return q.order_by(models.Occurrence.start_year.asc()).all()


# ---------------------------------------------------------
# SEARCH
# ---------------------------------------------------------

def search_species(db: Session, query_text: str, limit: int, offset: int):
    pattern = f"%{query_text.lower()}%"
    return (
        db.query(models.Species)
        .filter(
            or_(
                models.Species.common_name.ilike(pattern),
                models.Species.scientific_name.ilike(pattern),
            )
        )
        .order_by(models.Species.common_name.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )
