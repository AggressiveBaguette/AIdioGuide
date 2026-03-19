from loguru import logger
from string import Template
from typing import TYPE_CHECKING
from models.schemas import VerifiedResearchOutputConcatenated, EtapeParcours

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry

class RedactionService:
    def __init__(self, user_context: UserContext, registery : WorkerRegistry):
        self.user_context = user_context
        self.registery = registery

    def create_stop_text(self, stop: EtapeParcours, facts_phase_1: VerifiedResearchOutputConcatenated, facts_phase_2: VerifiedResearchOutputConcatenated, messages_history: list[dict[str, str]]) -> str:
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

        facts = self._get_relevant_facts(stop, facts_phase_1, facts_phase_2)

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

    def _get_relevant_facts(self, stop: EtapeParcours, facts_phase_1: VerifiedResearchOutputConcatenated, facts_phase_2: VerifiedResearchOutputConcatenated) -> str:
        # We need to return all the relevant facts for the current stop
        # Phase 1: get all the facts with the ID returned by the LLM in the plan
        requested_facts_id = set(stop.faits_retenus)
        verified_facts_list = facts_phase_1.research_lines
        requested_facts = [fact for fact in verified_facts_list if fact.id in requested_facts_id]

        logger.debug(f"Requested Facts Id Phase 1: {requested_facts_id}")
        logger.debug(f"Requested facts Phase 1: {requested_facts}")
        phase_1_response = "\n".join(requested_facts)

        #Phase 2: The LLM requested new researches, so it does not know the ID, we have to get them by name
        requested_facts_names = {brief.name for brief in stop.briefs_recherche_additionnelle}
        verified_facts_list = facts_phase_2.research_lines
        requested_facts = [fact for fact in verified_facts_list if fact.title in requested_facts_names]
        
        logger.debug(f"stop.briefs_recherche_additionnelle : {stop.briefs_recherche_additionnelle}")
        logger.debug(f"verified_facts_list : {verified_facts_list}")
        logger.debug(f"Requested Facts Names Phase 2: {requested_facts_names}")
        logger.debug(f"Requested facts Phase 2: {requested_facts}")
        phase_2_response = "\n".join(requested_facts)

        response = phase_1_response + "\n" + phase_2_response
        return response
