# ecoatlas_api/routers/admin.py
"""
Admin router – reload database (Render free workaround)
"""

from fastapi import APIRouter, HTTPException, Query
from ..services.species_loader import reload_species_database

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

SECRET = "DEV_INIT_TOKEN"  # change si tu veux


@router.post("/reload")
async def reload_database(token: str = Query(...)):
    if token != SECRET:
        raise HTTPException(403, "Invalid token")

    count = reload_species_database()
    return {"status": "ok", "inserted": count}
