# routers/occurrences.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/species",
    tags=["occurrences"],
)


@router.get(
    "/{species_id}/occurrences",
    response_model=List[schemas.OccurrenceOut],
    summary="Occurrences d'une espèce",
    description=(
        "Retourne les occurrences géographiques d'une espèce (coordonnées lat/lng, années). "
        "Utilisé par le globe 3D et la carte."
    ),
)
def get_species_occurrences(
    species_id: int,
    from_year: Optional[int] = Query(
        None,
        description="Filtrer les occurrences à partir de cette année (incluse).",
    ),
    to_year: Optional[int] = Query(
        None,
        description="Filtrer les occurrences jusqu'à cette année (incluse).",
    ),
    source: Optional[str] = Query(
        None,
        description="Filtrer sur une source spécifique (ex: 'GBIF').",
    ),
    db: Session = Depends(get_db),
):
    # On vérifie d'abord que l'espèce existe
    species = crud.get_species_by_id(db, species_id=species_id)
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Espèce avec id={species_id} introuvable.",
        )

    occurrences = crud.get_occurrences_for_species(
        db,
        species_id=species_id,
        from_year=from_year,
        to_year=to_year,
        source=source,
    )

    return occurrences
