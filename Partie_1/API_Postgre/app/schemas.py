from pydantic import BaseModel
from datetime import date
from typing import Optional

# Résultats fonciers
class SilverResultatRead(BaseModel):
    id_unique: int
    code_postal: str
    commune: str
    date_mutation: date
    fichier_source: str
    nature_mutation: str
    nombre_pieces_principales: int
    surface_reelle_bati: float
    type_local: str
    valeur_fonciere: float
    part_date: date

    class Config:
        from_attributes = True

# Utilisateurs
class UtilisateurBase(BaseModel):
    nom: str
    email: str

class UtilisateurCreate(UtilisateurBase):
    mot_de_passe: str

class UtilisateurRead(UtilisateurBase):
    id: int

    class Config:
        from_attributes = True

# Authentification
class Token(BaseModel):
    access_token: str
    token_type: str

# Lire les résultats (adapté à la table réelle)
class ResultatRead(BaseModel):
    id_unique: str 
    code_postal: Optional[str]
    commune: Optional[str]
    valeur_fonciere: Optional[float]
    type_local: Optional[str]
    surface_reelle_bati: Optional[float]
    nature_mutation: Optional[str]
    fichier_source: Optional[str]
    date_mutation: Optional[date]
    nombre_pieces_principales: Optional[int]
    part_date: Optional[date]

    class Config:
        from_attributes = True