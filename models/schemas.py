from pydantic import BaseModel, Field, RootModel
from typing import List, Literal, Optional
from enum import Enum


class ResearchTopic(BaseModel):
    type: Literal["Lieu", "Theme"]
    name: str
    narrative_pitch: Optional(str) = None
    angle: Optional(str) = None

class Strategy(BaseModel):
    raw_output: str
    research_angle: Optional[str] = None
    strategy_thinking: Optional[str] = None
    research_topics: List[ResearchTopic] = Field(default_factory=list)

class FilNarratif(BaseModel):
    theme: str
    introduit_au: int
    developpe_aux: List[int] = Field(default_factory=list)
    clos_au: int
    resume: str

class ResearchOutputLine(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None
    affirmation: Optional[str] = None
    visual_proof: Optional[str] = None
    confidence: Optional[str] = None
    queries: Optional[List[str]] = None

class ResearchOutput(BaseModel):
    raw_output: str
    research_lines: List[ResearchOutputLine] = Field(default_factory=list)

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
    briefs_recherche_additionnelle: List[AdditionalResearchTopic] = Field(default_factory=list)

class AudioguidePlan(BaseModel):
    titre_audioguide: str
    strategie: str
    parcours: List[EtapeParcours]
    fils_narratifs: List[FilNarratif] = Field(default_factory=list)
    
# class ResearchItem(BaseModel):
#     category: str = Field(..., alias="c")
#     title: str = Field(..., alias="t")
#     analysis: str = Field(..., alias="a")
#     proof: str = Field(..., alias="p")
#     noise_level: str = Field(..., alias="nc")
#     queries: List[str] = Field(..., alias="q")

# class ResearchBlock(RootModel):
#     root: List[ResearchItem]

class ReplacementItem(BaseModel):
    expression: str
    langue: str
    phonemes_ipa: str
    type: str
    
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
    REDACTION_WITH_SSML="redaction_with_ssml"