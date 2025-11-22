# ecoatlas_api/services/wikidata_service.py
"""
Wikidata BIO fetcher
Convertit une espèce (nom scientifique) en infos bio complètes.
Ultra simplifié + cache interne pour vitesse.
"""

import httpx
from functools import lru_cache

WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/"


@lru_cache(maxsize=500)
def fetch_wikidata(scientific_name: str | None):
    if not scientific_name:
        return None

    # 1. Rechercher l’ID Wikidata
    search_url = (
        "https://www.wikidata.org/w/api.php"
        "?action=wbsearchentities"
        "&language=en"
        "&format=json"
        f"&search={scientific_name}"
    )

    try:
        res = httpx.get(search_url, timeout=5)
        data = res.json()
        hits = data.get("search", [])
        if not hits:
            return None
        qid = hits[0]["id"]
    except Exception:
        return None

    # 2. Récupérer les données de l'entité
    try:
        r2 = httpx.get(f"{WIKIDATA_API}{qid}.json", timeout=8)
        entity = list(r2.json()["entities"].values())[0]
        claims = entity.get("claims", {})
    except Exception:
        return None

    def get_prop(pid):
        """Retourne la valeur humaine d’une propriété Wikidata."""
        try:
            c = claims.get(pid, [])
            if not c:
                return None
            mainsnak = c[0]["mainsnak"]
            datav = mainsnak.get("datavalue", {})
            return datav.get("value")
        except Exception:
            return None

    # Propriétés utiles
    size_cm = get_prop("P2043")  # taille
    weight_kg = get_prop("P2067")  # poids
    lifespan = get_prop("P2250")  # durée de vie
    speed = get_prop("P2052")  # vitesse
    iucn = get_prop("P141")  # catégorie UICN
    diet = get_prop("P927")  # régime
    habitat = get_prop("P2973")  # habitat
    range_desc = get_prop("P181")  # description répartition
    image = get_prop("P18")

    # Convertir proprement
    def extract_amount(v):
        try:
            amount = float(v.get("amount"))
            return amount
        except Exception:
            return None

    return {
        "size_adult_cm": extract_amount(size_cm) if isinstance(size_cm, dict) else None,
        "weight_adult_kg": extract_amount(weight_kg) if isinstance(weight_kg, dict) else None,
        "lifespan_years": extract_amount(lifespan) if isinstance(lifespan, dict) else None,
        "speed_kmh": extract_amount(speed) if isinstance(speed, dict) else None,
        "iucn_status": iucn["id"] if isinstance(iucn, dict) else None,
        "diet": diet["id"] if isinstance(diet, dict) else None,
        "habitat": habitat["text"] if isinstance(habitat, dict) else None,
        "range_description": range_desc["text"] if isinstance(range_desc, dict) else None,
        "image_filename": image if isinstance(image, str) else None,
    }
