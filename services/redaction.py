from models.schemas import ResearchTopic
from loguru import logger
from string import Template
from typing import TYPE_CHECKING
from models.schemas import Strategy, AudioguidePlan, VerifiedResearchOutput

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry

class RedactionService:
    def __init__(self, user_context: UserContext, registery : WorkerRegistry):
        self.user_context = user_context
        self.registery = registery

    def create_stop_text(self, stop: AudioguidePlanStop, facts: VerifiedResearchOutput, ,messages_history: list[dict[str, str]]) -> str:
        with open("prompt/master_prompt_redaction.md", "r", encoding="utf-8") as f:
        template_brut = Template(f.read())

        stop_list = "\n".join([f"arrêt {stop.numero} : {stop.titre_etape}" for stop in self.plan.parcours])
        
        system_prompt = template_brut.substitute(
            title_audioguide = self.plan.titre_audioguide,
            city_name = self.user_context.city,
            language = self.user_context.language.code,
            strategie = self.plan.strategie,
            plan_global = stop_list,
            fils_narratifs = self.plan.fils_narratifs,
        )
        
        messages_history = []      

        worker = self.registery.claude_worker

        with open("prompt/prompt_instructions_redaction.md", "r", encoding="utf-8") as f:
            template_brut = Template(f.read())
        prompt = template_brut.substitute(
            nom_lieu = stop.localisation,
            titre_etape = stop.titre_etape,
            consigne_plume = stop.consigne_plume,
            transition_vers_suivant = stop.transition_vers_suivant,
            cible_duree_audio = stop.cible_duree_audio,
            faits_bruts = facts
        )

        # if stop.titre_etape == "La Conciergerie : Quand le Palais Devient Cage":
        if True:
            stop_text = worker.get_text(prompt, system_prompt=system_prompt, temperature = 0.8, cache = True, messages_history = messages_history)
            self.registery.storage.save(Category.REDACTION, self.user_context, stop_text, id = stop.numero)
            messages_history.append({"role": "assistant", "content": stop_text})

