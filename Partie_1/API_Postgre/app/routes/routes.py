from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas
from app.security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()

# Limiteur de requêtes basé sur l'adresse IP ou le token
limiter = Limiter(key_func=lambda request: request.headers.get("authorization", get_remote_address(request)))

# Création d'une session DB pour chaque requête
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------
# 🔐 Route de création utilisateur
# -----------------------
@router.post("/utilisateurs/", response_model=schemas.UtilisateurRead)
@limiter.limit("5/minute")
def create_user(
    request: Request,
    user: schemas.UtilisateurCreate,
    db: Session = Depends(get_db)
):
    if db.query(models.Utilisateur).filter_by(email=user.email).first():
        raise HTTPException(status_code=400, detail="Email déjà enregistré")

    hashed_password = get_password_hash(user.mot_de_passe)
    db_user = models.Utilisateur(
        nom=user.nom,
        email=user.email,
        mot_de_passe=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# -----------------------
# 🔐 Route de connexion / login
# -----------------------
@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.Utilisateur).filter_by(email=form_data.username).first()

    if not user or not verify_password(form_data.password, user.mot_de_passe):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}