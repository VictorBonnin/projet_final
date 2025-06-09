# app/routes/resultats.py
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas
from app.security import verify_token
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/resultats", response_model=List[schemas.ResultatRead])
@limiter.limit("5/minute")
def get_resultats(
    request: Request,
    code_postal: str = Query(None),
    commune: str = Query(None),
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(verify_token),
):
    query = db.query(models.SilverResultat)
    if code_postal:
        query = query.filter(models.SilverResultat.code_postal == code_postal)
    if commune:
        query = query.filter(models.SilverResultat.commune.ilike(f"%{commune}%"))
    return query.limit(100).all()