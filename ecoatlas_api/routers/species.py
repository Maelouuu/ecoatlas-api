# ecoatlas_api/routers/species.py
"""
Species Router – PRO VERSION
Espèces + détails + bio externe Wikidata + images.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from .. import crud, schemas, models
from ..services.wikidata_service import fetch_wikidata
from ..services.wikimedia_service import wikimedia_image_url

router = APIRouter(
    prefix="/species",
    tags=["species"],
)


# ---------------------------------------------------------
# LIST
# ---------------------------------------------------------

@router.get(
    "",
    response_model=List[schemas.SpeciesSummary],
    summary="Lister les espèces (pro)",
)
def list_species(
    year: Optional[int] = Query(None),
    life_zone: Optional[str] = Query(None),
    biome: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
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


# ---------------------------------------------------------
# DETAIL
# ---------------------------------------------------------

@router.get(
    "/{species_id}",
    response_model=schemas.SpeciesDetail,
    summary="Détail complet d'une espèce",
)
def get_species_detail(
    species_id: int,
    include: str | None = Query(None),
    db: Session = Depends(get_db),
):
    sp = crud.get_species_by_id(db, species_id)
    if not sp:
        raise HTTPException(404, f"Espèce id={species_id} inconnue")

    return sp


# ---------------------------------------------------------
# BIO WIKIDATA
# ---------------------------------------------------------

@router.get(
    "/{species_id}/bio",
    response_model=schemas.SpeciesBio,
    summary="Informations biologiques externes via Wikidata",
)
def get_species_bio(species_id: int, db: Session = Depends(get_db)):
    sp = crud.get_species_by_id(db, species_id)
    if not sp:
        raise HTTPException(404, "Espèce inconnue")

    data = fetch_wikidata(sp.scientific_name)
    if not data:
        raise HTTPException(404, "Données Wikidata introuvables")

    # Convertir image
    img_url = None
    if data.get("image_filename"):
        img_url = wikimedia_image_url(data["image_filename"])

    return schemas.SpeciesBio(
        id=sp.id,
        common_name=sp.common_name,
        scientific_name=sp.scientific_name,
        diet=data.get("diet"),
        lifespan_years=data.get("lifespan_years"),
        habitat=data.get("habitat"),
        speed_kmh=data.get("speed_kmh"),
        iucn_status=data.get("iucn_status"),
        size_adult_cm=data.get("size_adult_cm"),
        weight_adult_kg=data.get("weight_adult_kg"),
        range_description=data.get("range_description"),
        photo_url=img_url,
    )


# ---------------------------------------------------------
# IMAGES (alias simple)
# ---------------------------------------------------------

@router.get(
    "/{species_id}/images",
    summary="Récupère une image HD via Wikidata/Wikimedia",
)
def get_species_image(species_id: int, db: Session = Depends(get_db)):
    sp = crud.get_species_by_id(db, species_id)
    if not sp:
        raise HTTPException(404)

    data = fetch_wikidata(sp.scientific_name)
    if not data:
        return {"photo_url": None}

    if not data.get("image_filename"):
        return {"photo_url": None}

    return {"photo_url": wikimedia_image_url(data["image_filename"])}
