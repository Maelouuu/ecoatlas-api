# schemas.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# -------------------------------------------------------------------
# Occurrences (points sur le globe)
# -------------------------------------------------------------------
class OccurrenceOut(BaseModel):
    id: int
    lat: float
    lng: float
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    source: Optional[str] = None

    class Config:
        orm_mode = True


# -------------------------------------------------------------------
# Sources (comparateur de données)
# -------------------------------------------------------------------
class SourceOut(BaseModel):
    id: int
    source_name: str
    field_name: str
    value_raw: Optional[str] = None
    value_numeric: Optional[float] = None
    last_check_date: Optional[datetime] = None

    class Config:
        orm_mode = True


# -------------------------------------------------------------------
# Species (base commune)
# -------------------------------------------------------------------
class SpeciesBase(BaseModel):
    common_name: Optional[str] = None
    scientific_name: str
    life_zone: Optional[str] = None
    biome: Optional[str] = None
    population: Optional[float] = None
    size_newborn_cm: Optional[float] = None
    size_adult_cm: Optional[float] = None
    weight_newborn_kg: Optional[float] = None
    weight_adult_kg: Optional[float] = None
    photo_url: Optional[str] = None
    photo_key: Optional[str] = None


class SpeciesSummary(SpeciesBase):
    """
    Version 'liste' utilisée pour l'écran principal :
    /species?year=...&life_zone=...
    """

    id: int
    occurrences: List[OccurrenceOut] = []

    class Config:
        orm_mode = True



class SpeciesDetail(SpeciesBase):
    """
    Version détaillée pour la fiche d'une espèce :
    inclut les occurrences et les sources.
    """

    id: int
    gbif_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    occurrences: List[OccurrenceOut] = []
    sources: List[SourceOut] = []

    class Config:
        orm_mode = True


# -------------------------------------------------------------------
# Bio enrichie d'une espèce (données externes)
# -------------------------------------------------------------------
class SpeciesBioOut(BaseModel):
    id: int
    common_name: Optional[str] = None
    scientific_name: Optional[str] = None

    life_zone: Optional[str] = None
    biome: Optional[str] = None

    population: Optional[float] = None
    size_adult_cm: Optional[float] = None
    weight_adult_kg: Optional[float] = None

    # Champs issus majoritairement de Wikidata / Wikimedia
    diet: Optional[str] = None
    lifespan_years: Optional[float] = None
    habitat: Optional[str] = None
    range_description: Optional[str] = None
    iucn_status: Optional[str] = None
    speed_kmh: Optional[float] = None

    photo_url: Optional[str] = None


# -------------------------------------------------------------------
# Modèles pour la recherche et les filtres
# -------------------------------------------------------------------
class SpeciesSearchFilters(BaseModel):
    """
    Modèle facultatif si tu veux documenter les filtres côté Swagger.
    Tu pourras aussi directement utiliser les query params.
    """

    year: Optional[int] = None
    life_zone: Optional[str] = None
    biome: Optional[str] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0


# Si plus tard tu veux créer/modifier des espèces
# via l'API d'admin, tu pourras définir :
#
# class SpeciesCreate(SpeciesBase):
#     gbif_id: Optional[int] = None
#
# class SpeciesUpdate(BaseModel):
#     ... (tous les champs optionnels)
