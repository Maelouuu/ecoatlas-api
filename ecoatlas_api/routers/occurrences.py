# ecoatlas_api/routers/occurrences.py
"""
Occurrences Router – PRO VERSION
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from .. import crud, schemas

router = APIRouter(
    prefix="/occurrences",
    tags=["occurrences"],
)


@router.get(
    "/{species_id}",
    response_model=List[schemas.OccurrenceOut],
    summary="Occurrences filtrées",
)
def get_occurrences(
    species_id: int,
    from_year: Optional[int] = Query(None),
    to_year: Optional[int] = Query(None),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    occ = crud.get_occurrences_for_species(
        db,
        species_id=species_id,
        from_year=from_year,
        to_year=to_year,
        source=source,
    )
    return occ
