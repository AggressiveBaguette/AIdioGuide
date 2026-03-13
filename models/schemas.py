from pydantic import BaseModel, Field, RootModel
from typing import List, Literal, Optional


class FaitRetenu(BaseModel):
    # On force les 4 catégories prévues par le prompt Forensic
    categorie: Literal["F", "P", "S", "C"]
    titre: str
    affirmation: str
    preuve_visuelle: str

class RechercheAdditionnelle(BaseModel):
    name: str
    angle: str


class EtapeParcours(BaseModel):
    numero: int
    type: Literal["Vestige_Majeur", "Respiration_Contexte"]
    titre_etape: str
    localisation: str
    # Optional car la première étape n'a pas de transition
    transition_vers_prochain: Optional[str] = None
    consigne_plume: str
    cible_duree_audio: str
    is_grand_format: bool
    # Listes vides acceptées selon les règles de ton prompt
    faits_retenus: List[str] = Field(default_factory=list)
    briefs_recherche_additionnelle: List[RechercheAdditionnelle] = Field(default_factory=list)

class AudioguidePlan(BaseModel):
    titre_audioguide: str
    strategie: str
    parcours: List[EtapeParcours]
    
class ResearchItem(BaseModel):
    category: str = Field(..., alias="c")
    title: str = Field(..., alias="t")
    analysis: str = Field(..., alias="a")
    proof: str = Field(..., alias="p")
    noise_level: str = Field(..., alias="nc")
    queries: List[str] = Field(..., alias="q")

class ResearchBlock(RootModel):
    root: List[ResearchItem]
