from loguru import logger
from string import Template
from typing import TYPE_CHECKING
from models.schemas import Strategy, AudioguidePlan, VerifiedResearchOutput, VerifiedResearchOutputConcatenated

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry

class PlanService:
    def __init__(self, user_context: UserContext, registry : WorkerRegistry):
        self.user_context = user_context
        self.registry = registry

    async def define_plan(self, strategy: Strategy, verified_facts: VerifiedResearchOutputConcatenated) -> AudioguidePlan:
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

        research_concatenated = self._prepare_research_for_plan(verified_facts)

        worker = self.registry.claude_worker
        plan = await worker.get_json(AudioguidePlan, "--", system_prompt=prompt, research_block_1=research_concatenated, temperature = 0.7)
        return plan

    def _prepare_strategy_for_plan(self, strategy: Strategy) -> str:
        # formating a DSV to send the initial strategy to the LLM that is going to perform the planification
        response_list = []
        for topic in strategy.research_topics:
            pitch = topic.narrative_pitch or ""

            parts = [topic.type, topic.name, pitch]
            response_list.append("|".join(parts))
        return "\n".join(response_list)
        

    def _prepare_research_for_plan(self, research_concatenated: VerifiedResearchOutputConcatenated) -> str:
        return research_concatenated.raw_output

        