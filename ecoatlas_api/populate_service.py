# ecoatlas_api/populate_service.py
"""
Service de remplissage de la base Species + Occurrence
→ utilisé par une route admin (utile sur Render free, sans shell).
"""

import json
import random
from pathlib import Path
from sqlalchemy.orm import Session

from .database import SessionLocal
from . import models


# -----------------------------------------------------
# Charger les 500 espèces depuis species_base.json
# -----------------------------------------------------
DATA_PATH = Path(__file__).resolve().parent / "data" / "species_base.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    SPECIES_DATA = json.load(f)


# -----------------------------------------------------
# Génération d'années pour le slider
# -----------------------------------------------------
def generate_years(seed: str) -> tuple[int, int]:
    rnd = random.Random(seed)
    start = rnd.randint(1900, 2015)
    duration = rnd.randint(0, 30)
    end = min(2025, start + duration)
    return start, end


def infer_life_zone(common_name: str | None, biome: str | None) -> str | None:
    """
    Devine une life_zone ("marin", "volant", "terrestre")
    à partir du nom + biome. C'est approximatif mais suffisant pour les filtres.
    """
    txt = f"{common_name or ''} {biome or ''}".lower()

    if any(w in txt for w in ["océan", "ocean", "mer", "récif", "recif"]):
        return "marin"

    if any(w in txt for w in ["aigle", "perroquet", "ara", "oiseau", "pingouin", "bird"]):
        return "volant"

    return "terrestre"


def reset_tables(db: Session) -> None:
    """Supprime toutes les occurrences + espèces."""
    db.query(models.Occurrence).delete()
    db.query(models.Species).delete()
    db.commit()


def populate_species_database() -> int:
    """
    Vide complètement les tables species + occurrences,
    puis insère les 500 espèces de species_base.json.
    Renvoie le nombre d'espèces créées.
    """
    db = SessionLocal()
    created = 0

    try:
        reset_tables(db)

        for sp_raw in SPECIES_DATA:
            common = sp_raw.get("common_name")
            sci = sp_raw.get("scientific_name")
            biome = sp_raw.get("biome")
            life_zone = infer_life_zone(common, biome)

            # Création de l'espèce (on laisse population, poids, tailles à None pour l'instant)
            species = models.Species(
                gbif_id=None,
                common_name=common,
                scientific_name=sci,
                life_zone=life_zone,
                biome=biome,
            )
            db.add(species)
            db.commit()
            db.refresh(species)

            # Occurrences
            for idx, o in enumerate(sp_raw.get("occurrences", [])):
                lat = float(o["lat"])
                lng = float(o["lng"])
                start, end = generate_years(f"{species.id}:{idx}")

                occ = models.Occurrence(
                    species_id=species.id,
                    lat=lat,
                    lng=lng,
                    start_year=start,
                    end_year=end,
                    source="MANUAL",
                )
                db.add(occ)

            db.commit()
            created += 1

        return created

    finally:
        db.close()
