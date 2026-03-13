import asyncio
from string import Template
from loguru import logger
from models.context import UserContext
from models.registry import WorkerRegistry
from models.schemas import AudioguidePlan
from workers.exa import ExaSearch
from workers.claude import Claude
from workers.storage import SaveFiles
from Poubelle.simulated_integration import SimulationStrategy, SimulationPlan
from services.researcher import Research
from workers.gemini import Gemini
from Poubelle.schemas import Category

class Orchestration:
    def __init__(self, user_context: UserContext, registery: WorkerRegistry):
        self.user_context = user_context
        self.registery = registery

        with open("prompt/master_prompt.txt", "r", encoding="utf-8") as f:
            template_brut = Template(f.read())

        self.system_prompt = template_brut.substitute(
            city=user_context.city,
            language=user_context.language
        )

    async def strategy_agent(self, is_simulation=False):
        """First, define the strategy"""
        if self.registery.storage.does_exist(Category.STRATEGY, self.user_context):
            logger.info("Strategy already created!")
            self.strategy = self.registery.storage.loads(Category.STRATEGY, self.user_context)

        else:
            with open("prompt/master_prompt_strategy.md", "r", encoding="utf-8") as f:
                template_brut = Template(f.read())
            content = template_brut.substitute(
                city_name=self.user_context.city,
                language=self.user_context.language,
                user_profile=self.user_context.comment
            )
            logger.debug(f"content : {content}")

            if is_simulation:
                worker = self.registery.simulation_strategy
            else:
                worker = self.registery.claude_worker

            self.strategy = worker.get_text(content = content, temperature = 1)

            logger.debug(f"Strategy : {self.strategy}")
            self.registery.storage.save(Category.STRATEGY, self.user_context, str(self.strategy))

    async def plan(self, is_simulation):
        if self.registery.storage.does_exist(Category.PLAN, self.user_context):
            logger.info("Plan already created!")
            plan = self.registery.storage.loads(Category.PLAN, self.user_context)
            return plan

        else:
            with open("prompt/master_prompt_planification.md", "r", encoding="utf-8") as f:
                template_brut = Template(f.read())
            
            logger.debug(f"plan_stratege : {self.strategy}")

            # We need reasearch_phase_1 to be a string to be sent to the LLM. We add an ID in front of each research topic to save tokens and references
            research_table = self.registery.storage.loads_all_verifed_research(self.user_context, "phase_1")
            all_lines = [line for block in research_table for line in block.split("\n")]
            self.research_phase_1 = "\n".join(f"ID_{i}|{line}" for i, line in enumerate(all_lines, 1))

            logger.debug(f"research_phase_1 : {self.research_phase_1[:1000]}")

            logger.debug(f"template_brut : {template_brut}")

            prompt = template_brut.substitute(
                city_name=self.user_context.city,
                angle_recherche=self.research_angle,
                strategie_globale=self.strategy_thinking,
                plan_stratege=self.strategy
        )

            if is_simulation:
                worker = self.registery.simulation_plan
            else:
                worker = self.registery.claude_worker

            plan = worker.get_json(AudioguidePlan, "--", system_prompt=prompt, research_block_1=self.research_phase_1, temperature = 0.7)
            self.registery.storage.save(Category.PLAN, self.user_context, plan)
            logger.info("Plan created!")
            logger.debug(f"Plan : {plan}")
            return plan

    async def parse_strategy(self):
        strategy_line = self.strategy.split("\n")
        research_topic_list = []

        for line in strategy_line:
            logger.debug(f"line : {line}")
            input = line.split("|")
            match input[0]:
                case "STRATEGIE":
                    self.strategy_thinking = input[1]
                case "ANGLE_RECHERCHE":
                    self.research_angle = input[1]
                case "Lieu":
                    research_topic_list.append({
                        "type":input[0],
                        "name":input[1],
                        "angle":input[2]
                    })
                case "Theme":
                    research_topic_list.append({
                        "type":input[0],
                        "name":input[1],
                        "angle":input[2]
                    })                  

        return research_topic_list

    async def research(self, phase, is_simulation=False):
        coroutine_search_list = []

        research_topic_list = await self.parse_strategy()

        logger.debug(f"Strategy : {self.strategy}")
        for research_topic in research_topic_list:
            logger.info(f"Recherche pour le monument : {research_topic["name"]}")

            # if research_topic["name"] in ["Arènes de Lutèce", "Les murailles médiévales - de Philippe Auguste à Charles V",  "Île de la Cité - Palais de la Cité", "Les Juifs de Paris et les expulsions capétiennes", "Les Templiers à Paris - Le Temple et sa fin"]:  #
            # if research_topic["name"] in ["Arènes de Lutèce"]:      
            if True:        
                research = Research(self.user_context, research_topic, phase, self.registery, self.research_angle)
                coroutine_search_list.append(research.get_research_results(is_simulation))

        logger.debug(f"coroutine_search_list : {coroutine_search_list}")
        await asyncio.gather(*coroutine_search_list)
        logger.debug("Orchestration Research: Gather terminé")

        # We create a file with all verified research from the given phase
        self._bundle_all_verified_research(phase)
    
    def _bundle_all_verified_research(self, phase):
        list = self.registery.storage.loads_all_verifed_research(self.user_context, phase)
        concatened_research = "\n-----\n".join(list)
        self.registery.storage.save(Category.VERIFIED_RESEARCH_CONCATENATED, self.user_context, concatened_research)



async def orchestrator(user_context: UserContext):
    registery = WorkerRegistry(
        search_worker=ExaSearch(),
        claude_worker=Claude(),
        storage=SaveFiles(),
        simulation_strategy=SimulationStrategy(),
        simulation_plan=SimulationPlan(),
        gemini_worker=Gemini(),
        # simulation_content_prospector=SimulationContentProspector(),
    )

    logger.info("DEBUT DE LA STRATEGIE")
    orchestration = Orchestration(user_context, registery)
    await orchestration.strategy_agent(is_simulation=False)
    logger.info("FIN DE LA STRATEGIE")

    logger.info("DEBUT DE LA RECHERCHE")
    await orchestration.research("phase_1", is_simulation=False)
    logger.info("FIN DE LA RECHERCHE")

    await orchestration.plan(is_simulation=False)
