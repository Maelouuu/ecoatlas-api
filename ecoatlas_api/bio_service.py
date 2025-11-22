# ecoatlas_api/bio_service.py
"""
Service pour récupérer / enrichir les infos biologiques d'une espèce
à partir de Wikidata + Wikimedia Commons.

Objectif :
- Donner à la page /species/[id] des valeurs réelles (taille, poids, etc.)
- Sans casser le modèle SQL existant.
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import httpx
from sqlalchemy.orm import Session

from . import models, schemas

WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY_URL = "https://www.wikidata.org/wiki/Special:EntityData/{id}.json"
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"


# ----------------------------- OUTILS JSON -----------------------------


def _safe_first_claim(claims: Dict[str, Any], prop: str) -> Optional[Dict[str, Any]]:
    arr = claims.get(prop)
    if not arr:
        return None
    try:
        return arr[0]["mainsnak"]["datavalue"]["value"]
    except Exception:
        return None


def _extract_quantity(value: Any) -> Optional[float]:
    try:
        return float(value.get("amount"))
    except Exception:
        return None


def _extract_year_from_time(value: Any) -> Optional[float]:
    try:
        time_str = value.get("time")  # ex "+00000001970-01-01T00:00:00Z"
        if not time_str or len(time_str) < 5:
            return None
        return float(time_str[1:5])
    except Exception:
        return None


# ------------------------- WIKIDATA (bio) ------------------------------


def _fetch_wikidata_entity_id(scientific_or_common_name: str) -> Optional[str]:
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": scientific_or_common_name,
        "limit": 1,
    }
    with httpx.Client(timeout=10.0) as client:
        r = client.get(WIKIDATA_SEARCH_URL, params=params)
        r.raise_for_status()
        data = r.json()

    results = data.get("search") or []
    if not results:
        return None
    return results[0]["id"]  # ex "Q140"


def _fetch_wikidata_entity_data(entity_id: str) -> Optional[Dict[str, Any]]:
    url = WIKIDATA_ENTITY_URL.format(id=entity_id)
    with httpx.Client(timeout=10.0) as client:
        r = client.get(url)
        r.raise_for_status()
        data = r.json()
    entities = data.get("entities") or {}
    return entities.get(entity_id)


def fetch_bio_from_wikidata(scientific_name: Optional[str], common_name: Optional[str]) -> Dict[str, Any]:
    """Renvoie un dict avec les infos bio extraites de Wikidata.

    Si une info manque ou si l'appel rate, on renvoie juste moins de champs.
    """
    name = scientific_name or common_name
    if not name:
        return {}

    try:
        entity_id = _fetch_wikidata_entity_id(name)
        if not entity_id:
            return {}
        ent = _fetch_wikidata_entity_data(entity_id)
        if not ent:
            return {}
    except Exception:
        return {}

    claims = ent.get("claims", {})
    descriptions = ent.get("descriptions", {})
    labels = ent.get("labels", {})

    def get_desc(lang: str) -> Optional[str]:
        v = descriptions.get(lang)
        return v.get("value") if v else None

    def get_label(lang: str) -> Optional[str]:
        v = labels.get(lang)
        return v.get("value") if v else None

    # Propriétés Wikidata utilisées (liste non exhaustive)
    # P2250: life expectancy
    # P2067: mass
    # P2048: height / length
    # P141: IUCN status
    # P2971: habitat
    # P1082: population
    # P439: speed
    # P18: image (géré plutôt via Wikimedia dans la pratique)

    life_val = _safe_first_claim(claims, "P2250")
    lifespan_years = _extract_quantity(life_val) if life_val else None

    mass_val = _safe_first_claim(claims, "P2067")
    weight_kg = _extract_quantity(mass_val) if mass_val else None

    size_val = _safe_first_claim(claims, "P2048")
    size_m = _extract_quantity(size_val) if size_val else None

    pop_val = _safe_first_claim(claims, "P1082")
    population = _extract_quantity(pop_val) if pop_val else None

    speed_val = _safe_first_claim(claims, "P439")
    speed_kmh = _extract_quantity(speed_val) if speed_val else None

    iucn_ent = _safe_first_claim(claims, "P141")
    iucn_status = None
    if isinstance(iucn_ent, dict):
        iucn_status = iucn_ent.get("id")

    habitat_ent = _safe_first_claim(claims, "P2971")
    habitat = None
    if isinstance(habitat_ent, dict):
        habitat = habitat_ent.get("id")

    summary = get_desc("fr") or get_desc("en")
    label_fr = get_label("fr")
    label_en = get_label("en")

    return {
        "lifespan_years": lifespan_years,
        "weight_kg": weight_kg,
        "size_m": size_m,
        "population": population,
        "speed_kmh": speed_kmh,
        "iucn_status": iucn_status,
        "habitat": habitat,
        "summary": summary,
        "label_fr": label_fr,
        "label_en": label_en,
    }


# ---------------------- WIKIMEDIA COMMONS (image) ---------------------


def fetch_photo_from_commons(scientific_name: Optional[str], common_name: Optional[str]) -> Optional[str]:
    """
    Retourne une URL directe d'image (800px) si possible.
    """
    name = scientific_name or common_name
    if not name:
        return None

    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "piprop": "thumbnail",
        "pithumbsize": 800,
        "titles": name,
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(WIKIMEDIA_API, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return None

    pages = data.get("query", {}).get("pages", {})
    for _, page in pages.items():
        thumb = page.get("thumbnail")
        if thumb and thumb.get("source"):
            return thumb["source"]

    return None


# --------------------------- FONCTION PRINCIPALE ----------------------


def build_species_bio(db: Session, species: models.Species) -> schemas.SpeciesBioOut:
    """
    Construit un objet SpeciesBioOut en combinant :
    - ce qu'on a déjà en base
    - ce qu'on récupère sur Wikidata / Wikimedia
    et on en profite pour remplir certains champs en base
      (photo_url, taille, poids, population) s'ils sont vides.
    """
    sci = species.scientific_name
    common = species.common_name

    wikidata = fetch_bio_from_wikidata(sci, common)

    # Photo (on essaie d'abord la valeur stockée en base, sinon Commons)
    photo_url = species.photo_url
    if not photo_url:
        photo_url = fetch_photo_from_commons(sci, common)
        if photo_url:
            species.photo_url = photo_url
            db.add(species)
            db.commit()
            db.refresh(species)

    # On ne surcharge pas si déjà rempli, mais on complète si c'est vide
    size_adult_cm = species.size_adult_cm
    if size_adult_cm is None and wikidata.get("size_m") is not None:
        size_adult_cm = wikidata["size_m"] * 100.0
        species.size_adult_cm = size_adult_cm

    weight_adult_kg = species.weight_adult_kg
    if weight_adult_kg is None and wikidata.get("weight_kg") is not None:
        weight_adult_kg = wikidata["weight_kg"]
        species.weight_adult_kg = weight_adult_kg

    population = species.population
    if population is None and wikidata.get("population") is not None:
        population = wikidata["population"]
        species.population = population

    # Commit si on a modifié quelque chose
    db.add(species)
    db.commit()
    db.refresh(species)

    bio = schemas.SpeciesBioOut(
        id=species.id,
        common_name=species.common_name,
        scientific_name=species.scientific_name,
        life_zone=species.life_zone,
        biome=species.biome,
        population=population,
        size_adult_cm=size_adult_cm,
        weight_adult_kg=weight_adult_kg,
        diet=None,  # à enrichir plus tard si on trouve un champ Wikidata stable
        lifespan_years=wikidata.get("lifespan_years"),
        habitat=wikidata.get("habitat"),
        range_description=None,
        iucn_status=wikidata.get("iucn_status"),
        speed_kmh=wikidata.get("speed_kmh"),
        photo_url=photo_url,
    )
    return bio
