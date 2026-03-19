from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Union
from enum import Enum


class ResearchTopic(BaseModel):
    type: Literal["Lieu", "Theme"]
    name: str
    narrative_pitch: Optional[str] = None
    angle: Optional[str] = None

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

class ResearchOutputLinePhase2(BaseModel):
    affirmation: str
    confidence: str
    queries: List[str]

class ResearchOutputLinePhase1(BaseModel):
    category: str
    title: str
    affirmation: str
    visual_proof: str
    confidence: str
    queries: List[str]

class ResearchOutput(BaseModel):
    raw_output: str
    research_lines: List[Union[ResearchOutputLinePhase1, ResearchOutputLinePhase2]] = Field(default_factory=list)

class VerifiedResearchOutputLine(BaseModel):
    category: Optional[str] = None
    title: str
    affirmation: str
    visual_proof: Optional[str] = None
    confidence: str

class VerifiedResearchOutput(BaseModel):
    raw_output: str
    research_lines: List[VerifiedResearchOutputLine] = Field(default_factory=list)

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
    briefs_recherche_additionnelle: List[ResearchTopic] = Field(default_factory=list)

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

ResearchOutput.model_rebuild()