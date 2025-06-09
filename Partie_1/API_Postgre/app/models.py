from sqlalchemy import Column, Integer, String, Float, Date
from app.database import Base

class SilverResultat(Base):
    __tablename__ = "silver_resultats"

    id_unique = Column(Integer, primary_key=True, index=True)
    code_postal = Column(String)
    commune = Column(String)
    date_mutation = Column(Date)
    fichier_source = Column(String)
    nature_mutation = Column(String)
    nombre_pieces_principales = Column(Integer)
    surface_reelle_bati = Column(Float)
    type_local = Column(String)
    valeur_fonciere = Column(Float)
    part_date = Column(Date)

class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    mot_de_passe = Column(String, nullable=False)