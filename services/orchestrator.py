import openai.types.realtime.realtime_transcription_session_create_request_param
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
        self.research_phases = {}

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
            self.plan = AudioguidePlan.model_validate_json(plan)

        else:
            with open("prompt/master_prompt_planification.md", "r", encoding="utf-8") as f:
                template_brut = Template(f.read())
            
            logger.debug(f"plan_stratege : {self.strategy}")


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

            plan = worker.get_json(AudioguidePlan, "--", system_prompt=prompt, research_block_1=self.research_phases["phase_1"], temperature = 0.7)
            self.registery.storage.save(Category.PLAN, self.user_context, plan)
            logger.info("Plan created!")
            logger.debug(f"Plan : {plan}")
            self.plan = AudioguidePlan.model_validate_json(plan)

    async def parse_plan(self):
        research_topic_list = []

        for stop in self.plan.parcours:
            logger.debug(f"Parse_plan stop : {stop}")
            for research_topic in stop.briefs_recherche_additionnelle:
                research_topic_list.append({
                    "type":"Deep_Dive",
                    "name":research_topic.name,
                    "angle":research_topic.angle
                })
        return research_topic_list
            

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

        if phase == "phase_1":
            # if phase_1, then we get the research_topic_list from strategy 
            # if phase 2, we get the research_topic_list from the plan
            research_topic_list = await self.parse_strategy()
        else:
            research_topic_list = await self.parse_plan()


        logger.debug(f"Strategy : {self.strategy}")
        for research_topic in research_topic_list:
            logger.info(f"Recherche pour le monument : {research_topic["name"]}")

            # if research_topic["name"] in ["Arènes de Lutèce", "Les murailles médiévales - de Philippe Auguste à Charles V",  "Île de la Cité - Palais de la Cité", "Les Juifs de Paris et les expulsions capétiennes", "Les Templiers à Paris - Le Temple et sa fin"]:  #
            # if research_topic["name"] in ["Arènes de Lutèce"]:   
            # if research_topic["name"] in ["démolition haussmannienne du tissu médiéval du parvis Notre-Dame"]:   
            if True:        
                research = Research(self.user_context, research_topic, phase, self.registery, self.research_angle)
                coroutine_search_list.append(research.get_research_results(is_simulation))

        logger.debug(f"coroutine_search_list : {coroutine_search_list}")
        await asyncio.gather(*coroutine_search_list)
        logger.debug("Orchestration Research: Gather terminé")

        self._bundle_all_verified_research(phase)


    def _bundle_all_verified_research(self, phase):
        list = self.registery.storage.loads_all_verifed_research(self.user_context, phase)
        concatened_research = "\n-----\n".join(list)
        self.registery.storage.save_research(Category.VERIFIED_RESEARCH_CONCATENATED, self.user_context, concatened_research, phase)
        
        all_lines = [line for block in list for line in block.split("\n")]
        self.research_phases[phase] = "\n".join(f"ID_{i}|{line}" for i, line in enumerate(all_lines, 1))

        logger.debug(f"research_phases_{phase} : {self.research_phases[phase][:1000]}")

    async def redaction(self, is_simulation=False):
        coroutine_search_list = []
        with open("prompt/master_prompt_redaction.md", "r", encoding="utf-8") as f:
            template_brut = Template(f.read())


        for stop in self.plan.parcours:
            logger.debug(f"Stop : {stop}")

            if self.registery.storage.does_exist(Category.REDACTION, self.user_context, id = stop.numero):
                logger.info(f"Redaction {stop.numero} - {stop.titre_etape} already created!")

            else:
                facts_phase_1, facts_phase_2 = await self.get_facts(stop)

                prompt = template_brut.substitute(
                    title_audioguide = self.plan.titre_audioguide,
                    city_name = self.user_context.city,
                    language = self.user_context.language,
                    strategie = self.plan.strategie,
                    nom_lieu = stop.localisation,
                    titre_etape = stop.titre_etape,
                    consigne_plume = stop.consigne_plume,
                    transition_vers_suivant = stop.transition_vers_suivant,
                    cible_duree_audio = stop.cible_duree_audio,
                )

                logger.debug(f"Content : {prompt}")
                logger.debug(f"Stop name : {stop.numero} - {stop.titre_etape}")
                if is_simulation:
                    worker = self.registery.simulation_plan
                else:
                    worker = self.registery.claude_worker

                # if stop.titre_etape == "La Conciergerie : Quand le Palais Devient Cage":
                if True:
                    stop_text = worker.get_text("--", system_prompt=prompt, research_block_1=facts_phase_1, research_block_2 = facts_phase_2, temperature = 0.8)
                    self.registery.storage.save(Category.REDACTION, self.user_context, stop_text, id = stop.numero)

    async def get_facts_phase_2(self, stop):
            requested_facts = stop.briefs_recherche_additionnelle

        


    async def get_facts(self, stop):
        # phase 1
        requested_facts_id = set(stop.faits_retenus)
        verified_facts_list = self.research_phases["phase_1"].split("\n")

        requested_facts = [fact for fact in verified_facts_list if fact.split("|")[0] in requested_facts_id]
        logger.debug(f"Requested Facts Id Phase 1: {requested_facts_id}")
        logger.debug(f"Requested facts Phase 1: {requested_facts}")
        phase_1_response = "\n".join(requested_facts)

        #phase 2
        requested_facts_names = {brief.name for brief in stop.briefs_recherche_additionnelle}
        verified_facts_list = self.research_phases["phase_2"].split("\n")
        requested_facts = [fact for fact in verified_facts_list if fact.split("|")[1] in requested_facts_names]
        logger.debug(f"stop.briefs_recherche_additionnelle : {stop.briefs_recherche_additionnelle}")

        logger.debug(f"verified_facts_list : {verified_facts_list}")
        logger.debug(f"Requested Facts Names Phase 2: {requested_facts_names}")
        logger.debug(f"Requested facts Phase 2: {requested_facts}")
        phase_2_response = "\n".join(requested_facts)

        return phase_1_response, phase_2_response
                




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

    logger.info("DEBUT DU PLAN")
    await orchestration.plan(is_simulation=False)
    logger.info("FIN DU PLAN")

    logger.info("DEBUT PHASE RECHERCHE 2")
    await orchestration.research("phase_2", is_simulation=False)
    logger.info("FIN PHASE RECHERCHE 2")

    logger.info("DEBUT DE LA REDACTION")
    await orchestration.redaction(is_simulation=False)
    logger.info("FIN DE LA REDACTION")
