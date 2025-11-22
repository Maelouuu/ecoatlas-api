# ecoatlas_api/models.py
"""
SQLAlchemy ORM models – PRO version
Species + Occurrence with Wikidata enrichment.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from .database import Base


class Species(Base):
    __tablename__ = "species"

    id = Column(Integer, primary_key=True, index=True)
    gbif_id = Column(Integer, nullable=True)
    common_name = Column(String(255), index=True)
    scientific_name = Column(String(255), index=True)
    life_zone = Column(String(50), nullable=True)
    biome = Column(String(255), nullable=True)

    # Enrichissement Wikidata (stockage léger)
    population = Column(Integer, nullable=True)
    size_adult_cm = Column(Float, nullable=True)
    weight_adult_kg = Column(Float, nullable=True)
    diet = Column(Text, nullable=True)
    lifespan_years = Column(Float, nullable=True)
    iucn_status = Column(String(50), nullable=True)
    habitat = Column(Text, nullable=True)
    speed_kmh = Column(Float, nullable=True)
    range_description = Column(Text, nullable=True)

    # Photo (Wikimedia URL)
    photo_url = Column(Text, nullable=True)

    occurrences = relationship("Occurrence", back_populates="species")

    __table_args__ = (
        Index("idx_species_common", "common_name"),
        Index("idx_species_scientific", "scientific_name"),
    )


class Occurrence(Base):
    __tablename__ = "occurrences"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("species.id", ondelete="CASCADE"))

    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)

    source = Column(String(50), default="MANUAL")

    species = relationship("Species", back_populates="occurrences")

    __table_args__ = (
        Index("idx_occ_species", "species_id"),
        Index("idx_occ_lat_lng", "lat", "lng"),
        Index("idx_occ_year", "start_year", "end_year"),
    )
