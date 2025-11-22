# ecoatlas_api/routers/search.py
"""
Recherche intelligente d'espèces
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import crud, schemas

router = APIRouter(
    prefix="/search",
    tags=["search"],
)


@router.get(
    "/species",
    response_model=List[schemas.SpeciesSummary],
)
def search_species(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return crud.search_species(db, query_text=q, limit=limit, offset=offset)
