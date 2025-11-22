# routers/species.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/species",
    tags=["species"],
)


@router.get(
    "",
    response_model=List[schemas.SpeciesSummary],
    summary="Lister les espèces",
    description=(
        "Retourne une liste d'espèces, filtrable par année, life_zone, biome et texte de recherche. "
        "Utilisée pour alimenter le globe et les listes dans l'app."
    ),
)
def list_species(
    year: Optional[int] = Query(
        None,
        description="Année de référence pour filtrer les espèces en fonction de leurs occurrences.",
    ),
    life_zone: Optional[str] = Query(
        None,
        description="Zone de vie : 'marin', 'terrestre', 'volant', etc.",
    ),
    biome: Optional[str] = Query(
        None,
        description="Biome : forêt tropicale, désert, etc.",
    ),
    search: Optional[str] = Query(
        None,
        description="Texte recherché dans les noms communs / scientifiques.",
    ),
    limit: int = Query(
        50,
        ge=1,
        le=200,
        description="Nombre maximum d'espèces à retourner (pagination).",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Décalage de départ pour la pagination.",
    ),
    db: Session = Depends(get_db),
):
    species = crud.get_species_list(
        db,
        year=year,
        life_zone=life_zone,
        biome=biome,
        search=search,
        limit=limit,
        offset=offset,
    )
    return species


@router.get(
    "/{species_id}",
    response_model=schemas.SpeciesDetail,
    summary="Détails d'une espèce",
    description=(
        "Renvoie la fiche détaillée d'une espèce, incluant ses occurrences et ses sources "
        "(pour le comparateur de données)."
    ),
)
def get_species_detail(
    species_id: int,
    db: Session = Depends(get_db),
):
    species = crud.get_species_by_id(db, species_id=species_id)
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Espèce avec id={species_id} introuvable.",
        )
    return species


@router.get(
    "/{species_id}/bio",
    response_model=schemas.SpeciesBioOut,
    summary="Bio enrichie d'une espèce",
    description="Combine les données EcoAtlas en base avec Wikidata/Wikimedia.",
)
def get_species_bio(
    species_id: int,
    db: Session = Depends(get_db),
):
    species = crud.get_species_by_id(db, species_id=species_id)
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Espèce avec id={species_id} introuvable.",
        )

    from ..bio_service import build_species_bio

    return build_species_bio(db, species)
