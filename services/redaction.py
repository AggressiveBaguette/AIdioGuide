from loguru import logger
from string import Template
from typing import TYPE_CHECKING
from models.schemas import VerifiedResearchOutputConcatenated, EtapeParcours, AudioguidePlan, VerifiedResearchOutputConcatenatedLine

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry

class RedactionService:
    def __init__(self, user_context: UserContext, registry : WorkerRegistry):
        self.user_context = user_context
        self.registry = registry

        with open("prompt/master_prompt_redaction.md", "r", encoding="utf-8") as f:
            self.template_system_prompt = Template(f.read())
        
        with open("prompt/prompt_instructions_redaction.md", "r", encoding="utf-8") as f:
            self.template_prompt_instructions = Template(f.read())


    async def create_stop_text(self, plan: AudioguidePlan, stop: EtapeParcours, facts_phase_1: VerifiedResearchOutputConcatenated, facts_phase_2: VerifiedResearchOutputConcatenated, messages_history: list[dict[str, str]]) -> str:

        stop_list = "\n".join([f"arrêt {stop.numero} : {stop.titre_etape}" for stop in plan.parcours])
        
        system_prompt = self.template_system_prompt.substitute(
            title_audioguide = plan.titre_audioguide,
            city_name = self.user_context.city,
            language = self.user_context.language.code,
            strategie = plan.strategie,
            plan_global = stop_list,
            fils_narratifs = plan.fils_narratifs,
        )
        
        facts = self._get_relevant_facts(stop, facts_phase_1, facts_phase_2)


        prompt = self.template_prompt_instructions.substitute(
            nom_lieu = stop.localisation,
            titre_etape = stop.titre_etape,
            consigne_plume = stop.consigne_plume,
            transition_vers_suivant = stop.transition_vers_suivant,
            cible_duree_audio = stop.cible_duree_audio,
            faits_bruts = facts
        )

        worker = self.registry.claude_worker
        stop_text = await worker.get_text(prompt, system_prompt=system_prompt, temperature = 0.8, cache = True, messages_history = messages_history)

        new_history = list(messages_history)
        new_history.append({"role": "user", "content": prompt})
        new_history.append({"role": "assistant", "content": stop_text})
        return stop_text, new_history

    def _get_relevant_facts(self, stop: EtapeParcours, facts_phase_1: VerifiedResearchOutputConcatenated, facts_phase_2: VerifiedResearchOutputConcatenated) -> str:
        # We need to return all the relevant facts for the current stop
        # Phase 1: get all the facts with the ID returned by the LLM in the plan
        requested_facts_id = set(stop.faits_retenus)
        verified_facts_list = facts_phase_1.research_lines
        requested_facts = [self._flatten_research_concatenated(fact) for fact in verified_facts_list if fact.id in requested_facts_id]

        logger.debug(f"Requested Facts Id Phase 1: {requested_facts_id}")
        logger.debug(f"Requested facts Phase 1: {requested_facts}")
        phase_1_response = "\n".join(requested_facts)

        #Phase 2: The LLM requested new researches, so it does not know the ID, we have to get them by name
        requested_facts_names = {brief.name for brief in stop.briefs_recherche_additionnelle}
        verified_facts_list = facts_phase_2.research_lines
        requested_facts = [self._flatten_research_concatenated(fact) for fact in verified_facts_list if fact.title in requested_facts_names]
        
        logger.debug(f"stop.briefs_recherche_additionnelle : {stop.briefs_recherche_additionnelle}")
        logger.debug(f"verified_facts_list : {verified_facts_list}")
        logger.debug(f"Requested Facts Names Phase 2: {requested_facts_names}")
        logger.debug(f"Requested facts Phase 2: {requested_facts}")
        phase_2_response = "\n".join(requested_facts)

        response = phase_1_response + "\n" + phase_2_response
        return response

    def _flatten_research_concatenated(self, research_concatenated: VerifiedResearchOutputConcatenatedLine) -> str:
        # transforming the json into DSV
        parts = [
            research_concatenated.id,
            research_concatenated.title,
            research_concatenated.affirmation,
            research_concatenated.visual_proof,
            research_concatenated.confidence
        ]
        return "|".join(str(part) for part in parts)

