# crud.py
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from . import models


# -------------------------------------------------------------------
# Species
# -------------------------------------------------------------------
def get_species_list(
    db: Session,
    *,
    year: Optional[int] = None,
    life_zone: Optional[str] = None,
    biome: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[models.Species]:
    """
    Récupère une liste d'espèces avec filtres optionnels :
    - year      : filtre en fonction des occurrences existantes à cette année
    - life_zone : "marin", "terrestre", "volant", etc.
    - biome     : biome textuel
    - search    : texte cherché dans common_name ou scientific_name
    - limit / offset : pagination simple
    """

    # Base : toutes les espèces
    query = db.query(models.Species)

    # Filtre life_zone
    if life_zone:
        query = query.filter(models.Species.life_zone == life_zone)

    # Filtre biome
    if biome:
        query = query.filter(models.Species.biome == biome)

    # Filtre de recherche texte
    if search:
        like_pattern = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(models.Species.common_name).like(like_pattern),
                func.lower(models.Species.scientific_name).like(like_pattern),
            )
        )

    # Filtre sur l'année basée sur les occurrences
    if year is not None:
        # On ne garde que les espèces qui ont au moins une occurrence
        # dont l'année englobe "year"
        query = (
            query.join(models.Occurrence, models.Species.id == models.Occurrence.species_id)
            .filter(
                and_(
                    # start_year <= year ou start_year NULL
                    or_(
                        models.Occurrence.start_year == None,  # noqa: E711
                        models.Occurrence.start_year <= year,
                    ),
                    # end_year >= year ou end_year NULL
                    or_(
                        models.Occurrence.end_year == None,  # noqa: E711
                        models.Occurrence.end_year >= year,
                    ),
                )
            )
            .distinct()
        )

    query = query.order_by(models.Species.scientific_name.asc())
    query = query.offset(offset).limit(limit)

    return query.all()


def get_species_by_id(db: Session, species_id: int) -> Optional[models.Species]:
    """
    Récupère une espèce par son ID interne.
    """
    return (
        db.query(models.Species)
        .filter(models.Species.id == species_id)
        .options(
            # les relations occurrences/sources sont en lazy="selectin",
            # donc elles seront chargées automatiquement lors de l'accès
        )
        .first()
    )


def get_species_by_gbif_id(db: Session, gbif_id: int) -> Optional[models.Species]:
    """
    Récupère une espèce par son identifiant GBIF (si défini).
    """
    return db.query(models.Species).filter(models.Species.gbif_id == gbif_id).first()


# -------------------------------------------------------------------
# Occurrences
# -------------------------------------------------------------------
def get_occurrences_for_species(
    db: Session,
    *,
    species_id: int,
    from_year: Optional[int] = None,
    to_year: Optional[int] = None,
    source: Optional[str] = None,
) -> List[models.Occurrence]:
    """
    Récupère les occurrences d'une espèce avec filtres optionnels :
    - from_year / to_year : plage temporelle
    - source : "GBIF", etc.
    """

    query = db.query(models.Occurrence).filter(models.Occurrence.species_id == species_id)

    if source:
        query = query.filter(models.Occurrence.source == source)

    if from_year is not None:
        query = query.filter(
            or_(
                models.Occurrence.start_year == None,  # noqa: E711
                models.Occurrence.start_year >= from_year,
            )
        )

    if to_year is not None:
        query = query.filter(
            or_(
                models.Occurrence.end_year == None,  # noqa: E711
                models.Occurrence.end_year <= to_year,
            )
        )

    return query.all()


# -------------------------------------------------------------------
# Sources (comparateur)
# -------------------------------------------------------------------
def get_sources_for_species(db: Session, species_id: int) -> List[models.Source]:
    """
    Récupère toutes les sources enregistrées pour une espèce.
    """
    return db.query(models.Source).filter(models.Source.species_id == species_id).all()


# -------------------------------------------------------------------
# Recherche dédiée (si tu veux un endpoint /search séparé)
# -------------------------------------------------------------------
def search_species(
    db: Session,
    *,
    query_text: str,
    limit: int = 50,
    offset: int = 0,
) -> List[models.Species]:
    """
    Recherche d'espèces par nom commun ou scientifique, sans autres filtres.
    Utilisée par /search/species.
    """

    like_pattern = f"%{query_text.lower()}%"

    query = (
        db.query(models.Species)
        .filter(
            or_(
                func.lower(models.Species.common_name).like(like_pattern),
                func.lower(models.Species.scientific_name).like(like_pattern),
            )
        )
        .order_by(models.Species.scientific_name.asc())
        .offset(offset)
        .limit(limit)
    )

    return query.all()


# -------------------------------------------------------------------
# Stats simples (optionnelles)
# -------------------------------------------------------------------
def count_species(db: Session) -> int:
    """
    Nombre total d'espèces.
    """
    return db.query(func.count(models.Species.id)).scalar() or 0


def count_occurrences_for_species(db: Session, species_id: int) -> int:
    """
    Nombre d'occurrences pour une espèce donnée.
    """
    return (
        db.query(func.count(models.Occurrence.id))
        .filter(models.Occurrence.species_id == species_id)
        .scalar()
        or 0
    )
