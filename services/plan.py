from models.schemas import ResearchTopic
from loguru import logger
from string import Template
from typing import TYPE_CHECKING
from models.schemas import Strategy, AudioguidePlan, VerifiedResearchOutput

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry

class PlanService:
    def __init__(self, user_context: UserContext, registery : WorkerRegistry):
        self.user_context = user_context
        self.registery = registery

    def define_plan(self, strategy: Strategy, verified_facts_list: list[VerifiedResearchOutput]) -> AudioguidePlan:
        with open("prompt/master_prompt_planification.md", "r", encoding="utf-8") as f:
            template_brut = Template(f.read())
        
        strategy_formatted = self._prepare_strategy_for_plan(strategy)
        logger.debug(f"strategy_formatted : {strategy_formatted}")

        prompt = template_brut.substitute(
            city_name=self.user_context.city,
            angle_recherche=strategy.research_angle,
            strategie_globale=strategy.strategy_thinking,
            plan_stratege=strategy_formatted
        )

        research_concatenated = self._prepare_research_for_plan(verified_facts_list)

        worker = self.registery.claude_worker
        plan = worker.get_json(AudioguidePlan, "--", system_prompt=prompt, research_block_1=research_concatenated, temperature = 0.7)
        return plan, research_concatenated

    def _prepare_strategy_for_plan(self, strategy: Strategy) -> str:
        # formating a DSV to send the initial strategy to the LLM that is going to perform the planification
        response_list = []
        for topic in strategy.research_topics:
            pitch = topic.narrative_pitch or ""
            angle = topic.angle or ""

            parts = [topic.type, topic.name, pitch, angle]
            response_list.append("|".join(parts))
        return "\n".join(response_list)
        
    def _prepare_research_for_plan(self, verified_facts_list: list[VerifiedResearchOutput]) -> str:
        # formating a DSV to send the research data to the LLM that is going to perform the planification. DSV is use instead of json to reduce the number of used tokens.
        response_list = []
        for facts in verified_facts_list:
            block_list = []
            for fact in facts.research_lines:
                category = fact.category or ""
                visual_proof = fact.visual_proof or ""
                parts = [category, fact.title, fact.affirmation, visual_proof, fact.confidence]
                block_list.append("|".join(parts))
            response_list.append("\n".join(block_list))
        logger.debug(f"_prepare_research_for_plan : {response_list}")
        return "\n----\n".join(response_list)

        