from fastapi import FastAPI, Request
from app.routes import routes, resultats
from app.database import Base, engine
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

# Crée les tables SQL si elles n'existent pas
Base.metadata.create_all(bind=engine)

# Configuration du rate limiter
limiter = Limiter(key_func=get_remote_address)

# Création de l'application FastAPI
app = FastAPI()
app.state.limiter = limiter

# Gestion d'erreur en cas de dépassement de la limite
@app.exception_handler(RateLimitExceeded)
def ratelimit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Trop de requêtes. Merci de patienter."},
    )

# Route d'accueil avec une limite de requêtes
@app.get("/")
@limiter.limit("5/minute")
async def root(request: Request):
    return {"message": "Bienvenue sur l'API PostgreSQL"}

# Inclusion des routes de l'application
app.include_router(routes.router)     # routes générales (/login, /utilisateurs)
app.include_router(resultats.router)