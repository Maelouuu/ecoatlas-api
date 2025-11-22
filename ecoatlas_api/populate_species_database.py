"""
populate_species_database.py

⚠️ MODE A : Écrase totalement les tables Species + Occurrence
→ Vide la base
→ Insère 500 espèces populaires
→ Génère 10 à 50 occurrences réalistes par espèce
"""

import json
import random
from datetime import datetime
from sqlalchemy.orm import Session

from ecoatlas_api.database import SessionLocal, engine
from ecoatlas_api import models


# -----------------------------------------------------
# 1. Charger notre fichier JSON 500 espèces
# -----------------------------------------------------

JSON_PATH = "ecoatlas_api/data/species_base.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    SPECIES_DATA = json.load(f)


# -----------------------------------------------------
# 2. Générer années cohérentes (pour slider)
# -----------------------------------------------------

def generate_years(seed: str):
    rnd = random.Random(seed)
    start = rnd.randint(1900, 2015)
    duration = rnd.randint(0, 30)
    end = min(2025, start + duration)
    return start, end


# -----------------------------------------------------
# 3. Réinitialisation des tables
# -----------------------------------------------------

def reset_tables(db: Session):
    """Supprime toutes les espèces + occurrences"""
    db.query(models.Occurrence).delete()
    db.query(models.Species).delete()
    db.commit()


# -----------------------------------------------------
# 4. Insérer une espèce
# -----------------------------------------------------

def insert_species(db: Session, sp_raw: dict):
    """
    sp_raw = entrée de species_base.json :
    {
      "id": ...,
      "common_name": ...,
      "scientific_name": ...,
      "biome": ...,
      "region": ...,
      "occurrences": [...]
    }
    """

    species = models.Species(
        common_name = sp_raw.get("common_name"),
        scientific_name = sp_raw.get("scientific_name"),
        life_zone = None,       # on peut déduire plus tard
        biome = sp_raw.get("biome"),
        population = None,
        size_newborn_cm = None,
        size_adult_cm = None,
        weight_newborn_kg = None,
        weight_adult_kg = None,
        photo_url = None,
        photo_key = None,
        region = sp_raw.get("region"),
        created_at = datetime.utcnow()
    )

    db.add(species)
    db.commit()
    db.refresh(species)

    # -------------------------------
    # Insérer occurrences
    # -------------------------------

    for idx, o in enumerate(sp_raw.get("occurrences", [])):
        lat = float(o["lat"])
        lng = float(o["lng"])
        start, end = generate_years(f"{species.id}:{idx}")

        occ = models.Occurrence(
            species_id = species.id,
            source = "MANUAL",
            lat = lat,
            lng = lng,
            start_year = start,
            end_year = end
        )
        db.add(occ)

    db.commit()

    return species


# -----------------------------------------------------
# 5. Script principal
# -----------------------------------------------------

def main():
    print("🔄 Connexion DB…")
    db = SessionLocal()

    print("❌ Suppression des anciennes espèces + occurrences…")
    reset_tables(db)

    print("🦁 Insertion des 500 nouvelles espèces…")
    for sp_raw in SPECIES_DATA:
        insert_species(db, sp_raw)

    print("✅ FINI : 500 espèces chargées avec succès.")
    db.close()


if __name__ == "__main__":
    main()
