# models.py
from datetime import datetime
from typing import List

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .database import Base


class Species(Base):
    """
    Table principale des espèces.
    On utilise un ID interne (int) comme clé primaire
    + un identifiant externe (par ex. GBIF) si besoin.
    """

    __tablename__ = "species"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Identifiants externes (ex: GBIF)
    gbif_id: Mapped[int | None] = mapped_column(Integer, index=True, unique=True, nullable=True)

    # Noms
    common_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scientific_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    # Catégorisations
    life_zone: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "marin", "terrestre", "volant"...
    biome: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Population (optionnelle, ex : population approximative)
    population: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Tailles (en cm)
    size_newborn_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    size_adult_cm: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Poids (en kg)
    weight_newborn_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_adult_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Images
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # URL absolue ou relative
    photo_key: Mapped[str | None] = mapped_column(String(255), nullable=True)  # si tu veux mapper vers une image locale

    # Métadonnées
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relations
    occurrences: Mapped[List["Occurrence"]] = relationship(
        "Occurrence",
        back_populates="species",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    sources: Mapped[List["Source"]] = relationship(
        "Source",
        back_populates="species",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Occurrence(Base):
    """
    Points géographiques où l'espèce est observée.
    Sert au globe / carte.
    """

    __tablename__ = "occurrences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    species_id: Mapped[int] = mapped_column(Integer, ForeignKey("species.id", ondelete="CASCADE"), index=True)

    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)

    # Années approximatives pour ton slider
    start_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Source (ex: "GBIF")
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    species: Mapped["Species"] = relationship("Species", back_populates="occurrences")


class Source(Base):
    """
    Comparateur de données.
    Permet de stocker, pour une espèce, plusieurs valeurs
    provenant de différentes API (GBIF, OBIS, iNat, etc.).
    """

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    species_id: Mapped[int] = mapped_column(Integer, ForeignKey("species.id", ondelete="CASCADE"), index=True)

    # Nom de la source : "GBIF", "OBIS", "iNaturalist", etc.
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Champ concerné : "population", "distribution", "threat_status", etc.
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Valeur brute renvoyée par la source (en texte ou JSON sérialisé)
    value_raw: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Valeur numérique approximative (si tu veux comparer des chiffres)
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)

    last_check_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    species: Mapped["Species"] = relationship("Species", back_populates="sources")
