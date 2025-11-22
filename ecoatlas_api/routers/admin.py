# ecoatlas_api/routers/admin.py
"""
Admin tools for Render Free – RESET + RELOAD database
"""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

from ..database import engine
from ..database import Base
from ..services.species_loader import reload_species_database

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

SECRET = "DEV_INIT_TOKEN"   # change si tu veux


# --------------------------------------------------------
# RESET DATABASE
# --------------------------------------------------------
@router.post("/reset")
def reset_database(token: str = Query(...)):
    if token != SECRET:
        raise HTTPException(403, "Invalid token")

    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        return {"status": "ok", "message": "Database reset done"}
    except SQLAlchemyError as e:
        raise HTTPException(500, f"Reset failed: {str(e)}")


# --------------------------------------------------------
# RELOAD DATABASE WITH SPECIES JSON
# --------------------------------------------------------
@router.post("/reload")
def reload_database(token: str = Query(...)):
    if token != SECRET:
        raise HTTPException(403, "Invalid token")

    try:
        inserted = reload_species_database()
        return {"status": "ok", "inserted": inserted}
    except SQLAlchemyError as e:
        raise HTTPException(500, f"Reload failed: {str(e)}")
