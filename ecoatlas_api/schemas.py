# ecoatlas_api/schemas.py
"""
Pydantic schemas – final version
Used for clean API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


# OCCURRENCE -----------------------------------------

class OccurrenceBase(BaseModel):
    lat: float
    lng: float
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    source: Optional[str] = None

    class Config:
        from_attributes = True


class OccurrenceOut(OccurrenceBase):
    id: int

    class Config:
        from_attributes = True


# SPECIES --------------------------------------------

class SpeciesBase(BaseModel):
    id: int
    common_name: Optional[str] = None
    scientific_name: Optional[str] = None
    life_zone: Optional[str] = None
    biome: Optional[str] = None

    class Config:
        from_attributes = True


class SpeciesSummary(SpeciesBase):
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True


class SpeciesDetail(SpeciesBase):
    population: Optional[int] = None
    size_adult_cm: Optional[float] = None
    weight_adult_kg: Optional[float] = None
    diet: Optional[str] = None
    lifespan_years: Optional[float] = None
    iucn_status: Optional[str] = None
    habitat: Optional[str] = None
    speed_kmh: Optional[float] = None
    range_description: Optional[str] = None

    photo_url: Optional[str] = None

    occurrences: List[OccurrenceOut] = []

    class Config:
        from_attributes = True


# BIO ENRICHIE (API /bio) ----------------------------

class SpeciesBio(BaseModel):
    id: int
    common_name: Optional[str] = None
    scientific_name: Optional[str] = None

    diet: Optional[str] = None
    lifespan_years: Optional[float] = None
    habitat: Optional[str] = None
    speed_kmh: Optional[float] = None
    iucn_status: Optional[str] = None
    size_adult_cm: Optional[float] = None
    weight_adult_kg: Optional[float] = None
    range_description: Optional[str] = None

    photo_url: Optional[str] = None

    class Config:
        from_attributes = True
