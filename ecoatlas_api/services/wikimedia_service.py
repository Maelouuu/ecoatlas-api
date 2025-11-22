# ecoatlas_api/services/wikimedia_service.py
"""
Convertir un nom de fichier Wikimedia en URL HD.
Compatible Expo Image.
"""

import hashlib

def wikimedia_image_url(filename: str | None, size: int = 800):
    """
    Convertit un nom de fichier Wikimedia en URL de type :
    https://upload.wikimedia.org/wikipedia/commons/...
    """
    if not filename:
        return None

    # Wikimedia hashing rules
    md5 = hashlib.md5(filename.encode("utf-8")).hexdigest()
    url = (
        f"https://upload.wikimedia.org/wikipedia/commons/"
        f"{md5[0]}/{md5[0:2]}/{filename}"
    )
    return url
