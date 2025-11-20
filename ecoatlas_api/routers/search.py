# routers/search.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/search",
    tags=["search"],
)


@router.get(
    "/species",
    response_model=List[schemas.SpeciesSummary],
    summary="Recherche d'espèces par nom",
    description=(
        "Recherche d'espèces par nom commun ou scientifique. "
        "Utilisé pour l'autocomplétion / barre de recherche dans l'application."
    ),
)
def search_species_endpoint(
    q: str = Query(
        ...,
        min_length=1,
        description="Texte à chercher dans les noms communs ou scientifiques.",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Nombre maximum de résultats.",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Décalage de départ (pagination).",
    ),
    db: Session = Depends(get_db),
):
    results = crud.search_species(db, query_text=q, limit=limit, offset=offset)
    if not results:
        # ce n'est pas forcément une erreur, mais ça peut être pratique
        # pour l'auto-complétion de savoir quand il n'y a rien.
        return []
    return results
