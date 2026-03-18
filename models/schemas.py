from pydantic import BaseModel, Field, RootModel
from typing import List, Literal, Optional
from enum import Enum


class FaitRetenu(BaseModel):
    # On force les 4 catégories prévues par le prompt Forensic
    categorie: Literal["F", "P", "S", "C"]
    titre: str
    affirmation: str
    preuve_visuelle: str

class RechercheAdditionnelle(BaseModel):
    name: str
    angle: str

class FilNarratif(BaseModel):
    theme: str
    introduit_au: int
    developpe_aux: List[int] = Field(default_factory=list)
    clos_au: int
    resume: str


class EtapeParcours(BaseModel):
    numero: int
    type: Literal["Vestige_Majeur", "Respiration_Contexte"]
    titre_etape: str
    localisation: str
    transition_vers_suivant: str | None = None
    consigne_plume: str
    cible_duree_audio: str
    is_grand_format: bool = False
    faits_retenus: List[str] = Field(default_factory=list)
    briefs_recherche_additionnelle: List[RechercheAdditionnelle] = Field(default_factory=list)

class AudioguidePlan(BaseModel):
    titre_audioguide: str
    strategie: str
    parcours: List[EtapeParcours]
    fils_narratifs: List[FilNarratif] = Field(default_factory=list)
    
class ResearchItem(BaseModel):
    category: str = Field(..., alias="c")
    title: str = Field(..., alias="t")
    analysis: str = Field(..., alias="a")
    proof: str = Field(..., alias="p")
    noise_level: str = Field(..., alias="nc")
    queries: List[str] = Field(..., alias="q")

class ResearchBlock(RootModel):
    root: List[ResearchItem]

class ReplacementItem(BaseModel):
    expression: str
    langue: str
    phonemes_ipa: str
    
class PhonemesList(BaseModel):
    replacement_list: List[ReplacementItem]

class Category(Enum):
    PLAN = "plan"
    STRATEGY = "strategy"
    RESEARCH = "research"
    REDACTION = "redaction"
    PROSPECTOR = "content_prospector"
    RESEARCH_CONCATENATED = "research_concatenated"
    VERIFIED_RESEARCH = "verified_research"
    VERIFIED_RESEARCH_CONCATENATED = "verified_research_concatenated"
    PHONEMES="phonemes"
    AUDIO="audio"