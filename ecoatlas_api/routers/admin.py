# ecoatlas_api/routers/admin.py
import os
from fastapi import APIRouter, HTTPException

from ..populate_service import populate_species_database

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

# Petit "secret" pour éviter que n'importe qui déclenche le remplissage
SECRET_TOKEN = os.getenv("ECOATLAS_ADMIN_TOKEN", "DEV_INIT_TOKEN")


@router.api_route("/populate_species", methods=["GET", "POST"])
def admin_populate_species(token: str):
    """
    Route d'initialisation :
    - vide toutes les espèces + occurrences
    - insère les 500 espèces du JSON
    À appeler UNE SEULE FOIS sur Render.
    """
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    count = populate_species_database()
    return {
        "status": "ok",
        "inserted_species": count,
    }
