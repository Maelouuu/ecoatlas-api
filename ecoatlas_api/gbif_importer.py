# gbif_importer.py

import asyncio
import httpx
from sqlalchemy.orm import Session

from .database import SessionLocal, engine
from . import models

GBIF_SPECIES_SEARCH = "https://api.gbif.org/v1/species/search"
GBIF_OCCURRENCES = "https://api.gbif.org/v1/occurrence/search"


async def fetch_json(client, url, params=None):
    r = await client.get(url, params=params, timeout=20.0)
    r.raise_for_status()
    return r.json()


async def import_species(limit=500):
    print(f"🔎 Import GBIF – récupération de {limit} espèces...")

    async with httpx.AsyncClient() as client:
        # 1. Récupérer une liste de taxons animaux (kingdom = Animalia)
        search_params = {
            "kingdomKey": 1,  # Animalia
            "limit": limit,
            "offset": 0
        }
        data = await fetch_json(client, GBIF_SPECIES_SEARCH, params=search_params)
        results = data.get("results", [])

        print(f"📌 {len(results)} espèces trouvées dans la liste GBIF")

        db: Session = SessionLocal()

        for idx, entry in enumerate(results):
            try:
                species = models.Species(
                    gbif_id=entry.get("key"),
                    scientific_name=entry.get("scientificName", "Unknown"),
                    common_name=entry.get("vernacularName"),
                    life_zone=None,
                    biome=None,
                    population=None,
                    size_newborn_cm=None,
                    size_adult_cm=None,
                    weight_newborn_kg=None,
                    weight_adult_kg=None,
                    photo_url=None,
                )
                db.add(species)
                db.commit()
                db.refresh(species)

                # 2. Récupérer les occurrences associées
                occ_params = {
                    "taxonKey": entry.get("key"),
                    "limit": 200,
                    "hasCoordinate": "true"
                }
                occ_data = await fetch_json(client, GBIF_OCCURRENCES, params=occ_params)
                occurrences = occ_data.get("results", [])

                for occ in occurrences:
                    if "decimalLatitude" in occ and "decimalLongitude" in occ:
                        occ_item = models.Occurrence(
                            species_id=species.id,
                            lat=occ["decimalLatitude"],
                            lng=occ["decimalLongitude"],
                            start_year=occ.get("year"),
                            end_year=occ.get("year"),
                            source="GBIF",
                        )
                        db.add(occ_item)

                # Ajouter entrée "source"
                src = models.Source(
                    species_id=species.id,
                    source_name="GBIF",
                    field_name="taxon",
                    value_raw=str(entry),
                )
                db.add(src)

                db.commit()

                print(f"  ✔ Importé {idx+1}/{limit} : {species.scientific_name}")

            except Exception as e:
                print(f"⚠️ Erreur import espèce {idx}: {e}")

        db.close()

    print("🎉 Import terminé !")


if __name__ == "__main__":
    asyncio.run(import_species())
