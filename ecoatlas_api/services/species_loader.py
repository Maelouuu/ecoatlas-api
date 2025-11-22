# ecoatlas_api/services/species_loader.py
"""
Species Loader – PRO VERSION
Charge les 500 espèces + occurrences.
"""

import json
import random
from pathlib import Path
from sqlalchemy.orm import Session

from ..database import SessionLocal
from .. import models


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "species_base.json"


def random_years(seed: str):
    rnd = random.Random(seed)
    start = rnd.randint(1900, 2015)
    end = min(start + rnd.randint(0, 25), 2025)
    return start, end


def reload_species_database() -> int:
    """Reset + Reload 500 species."""
    db = SessionLocal()

    # wipe
    db.query(models.Occurrence).delete()
    db.query(models.Species).delete()
    db.commit()

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0

    for sp in data:
        species = models.Species(
            common_name=sp["common_name"],
            scientific_name=sp["scientific_name"],
            life_zone=sp.get("life_zone"),
            biome=sp.get("biome"),
        )
        db.add(species)
        db.commit()
        db.refresh(species)

        for idx, o in enumerate(sp["occurrences"]):
            start, end = random_years(f"{species.id}:{idx}")

            db.add(
                models.Occurrence(
                    species_id=species.id,
                    lat=float(o["lat"]),
                    lng=float(o["lng"]),
                    start_year=start,
                    end_year=end,
                    source="MANUAL",
                )
            )

        db.commit()
        count += 1

    db.close()
    return count
