# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path


from .database import Base, engine
from . import models
from .routers import species, occurrences, search

# ---------------------------------------------------------
# Création des tables (si elles n'existent pas)
# ---------------------------------------------------------
# IMPORTANT : il faut importer models AVANT ce create_all,
# pour que SQLAlchemy connaisse toutes les classes.
models  # juste pour être sûr qu'il est importé
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------
# Initialisation de l'application FastAPI
# ---------------------------------------------------------
app = FastAPI(
    title="EcoAtlas API",
    description=(
        "API centrale pour l'application EcoAtlas. "
        "Fournit les espèces, leurs occurrences géographiques, "
        "et les données issues de différentes sources (GBIF, etc.)."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------
# CORS (pour autoriser l'app Expo / React Native à appeler l'API)
# ---------------------------------------------------------
# En dev, on peut ouvrir à tout le monde ("*").
# Plus tard, tu pourras restreindre aux domaines nécessaires.
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:19006",  
    "*",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Mount des fichiers statiques (images, etc.)
# ---------------------------------------------------------
# Tu pourras mettre tes images dans ecoatlas_api/static/images/
# et y accéder via /static/images/xxx.jpg
# Chemin absolu vers ecoatlas_api/static
STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
else:
    # On ne bloque pas le démarrage si le dossier n'existe pas
    print(f"[WARN] Static directory not found: {STATIC_DIR}. Skipping static mount.")

# ---------------------------------------------------------
# Inclusion des routers
# ---------------------------------------------------------
app.include_router(species.router)
app.include_router(occurrences.router)
app.include_router(search.router)


# ---------------------------------------------------------
# Endpoint de test
# ---------------------------------------------------------
@app.get("/", tags=["health"])
def read_root():
    return {
        "status": "ok",
        "message": "EcoAtlas API is running",
    }


# ---------------------------------------------------------
# Lancement en dev (python -m ecoatlas_api.main)
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "ecoatlas_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
