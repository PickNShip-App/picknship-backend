from fastapi import Header, HTTPException, Depends
from app.core.config import settings

def verify_api_key(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        scheme, key = authorization.split()
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    if key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
