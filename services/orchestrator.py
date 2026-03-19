import asyncio
from string import Template
from loguru import logger
from models.context import UserContext
from models.registry import WorkerRegistry
from models.schemas import AudioguidePlan, Strategy, VerifiedResearchOutputConcatenated, AudioguideFinalText, ContentStop, PhonemesList
from workers.exa import ExaSearch
from workers.claude import Claude
from workers.storage import SaveFiles
from workers.simulation import SimulationStrategy, SimulationPlan
from services.research.research_orchestrator import ResearchOrchestrator
from workers.gemini import Gemini
from services.phonemes_detection import PhonemDetection
from models.schemas import Category, VerifiedResearchOutput
from workers.azureTTS import AzureTTS
from services.audio_generation import AudioService
from config import TTS_LANGUAGES_NO_PHONEMES
from services.strategy import StrategyService
from services.plan import PlanService
from services.redaction import RedactionService


class Orchestration:
    def __init__(self, user_context: UserContext, registery: WorkerRegistry, audio_service: AudioService, strategy_service:StrategyService, plan_service:PlanService, redaction_service:RedactionService):
        self.user_context = user_context
        self.registery = registery
        self.audio_service = audio_service
        self.strategy_service = strategy_service
        self.plan_service = plan_service
        self.redaction_service = redaction_service
        

        with open("prompt/master_prompt.txt", "r", encoding="utf-8") as f:
            template_brut = Template(f.read())

        self.system_prompt = template_brut.substitute(
            city=user_context.city,
            language=user_context.language.code
        )

    async def strategy(self) -> Strategy:
        """First, define the strategy"""
        if self.registery.storage.does_exist(Category.STRATEGY, self.user_context):
            logger.info("Strategy already created!")
            strategy = self.registery.storage.loads(Category.STRATEGY, self.user_context)
            return self.strategy_service.parse_strategy(strategy)

        strategy = await self.strategy_service.define_strategy() 
        logger.debug(f"Strategy : {strategy}")
        self.registery.storage.save(Category.STRATEGY, self.user_context, strategy.raw_output)
        return strategy

    async def plan(self, strategy: Strategy, verified_facts_list: list[VerifiedResearchOutput]) -> AudioguidePlan:
        if self.registery.storage.does_exist(Category.PLAN, self.user_context):
            logger.info("Plan already created!")
            plan = self.registery.storage.loads(Category.PLAN, self.user_context, pydantic_model=AudioguidePlan)
            return plan

        plan = self.plan_service.define_plan(strategy, verified_facts_list)
        self.registery.storage.save(Category.PLAN, self.user_context, plan)
        plan = AudioguidePlan.model_validate_json(plan)
        logger.info(f"Plan created: {plan[100:]}")
        return plan

    async def research(self, phase, strategy: Strategy, plan: AudioguidePlan = None) -> list[VerifiedResearchOutput]:
        coroutine_search_list = []

        if phase == "phase_1":
            # if phase_1, then we get the research_topics from strategy 
            # if phase 2, we get the research_topics from the plan
            research_topic_list = strategy.research_topics
            logger.debug(f"Strategy : {strategy}")
        else:
            research_topic_list = [
                topic
                for stop in plan.parcours
                for topic in stop.briefs_recherche_additionnelle
            ]
            logger.debug(f"Research topic list : {research_topic_list}")

        research = ResearchOrchestrator(self.user_context, self.registery, phase)
        for research_topic in research_topic_list:
            logger.info(f"Recherche on topic : {research_topic.name}")

            # if research_topic.name in ["Arènes de Lutèce", "Les murailles médiévales - de Philippe Auguste à Charles V",  "Île de la Cité - Palais de la Cité", "Les Juifs de Paris et les expulsions capétiennes", "Les Templiers à Paris - Le Temple et sa fin"]:  #
            if True:        
                coroutine_search_list.append(research.get_research_results(research_topic, strategy.research_angle))

        logger.debug(f"coroutine_search_list : {coroutine_search_list}")
        verified_facts_list = await asyncio.gather(*coroutine_search_list)
        logger.debug("Orchestration Research: Gather done")

        research_concatenated = research.concatenate_verified_researches(verified_facts_list)

        return research_concatenated

    def create_history_redaction(self):
        pass

    async def redaction(self, plan: AudioguidePlan, verified_facts_list_phase_1: VerifiedResearchOutputConcatenated, verified_facts_list_phase_2: VerifiedResearchOutputConcatenated) -> AudioguideFinalText:
        # Redaction is sequential because we need the LLM to know what has been written during the first iterations to avoid any major repetition        
        messages_history = []
        content_list = AudioguideFinalText(stop = [])
        for stop in plan.parcours:
            logger.debug(f"Stop : {stop}")

            if self.registery.storage.does_exist(Category.REDACTION, self.user_context, id = stop.numero):
                logger.info(f"Redaction {stop.numero} - {stop.titre_etape} already created!")
                text = self.registery.storage.loads(Category.REDACTION, self.user_context, id = stop.numero)
                messages_history = self.registery.storage.loads(Category.REDACTION_HISTORY, self.user_context, id = stop.numero)

            else:

                text, messages_history = self.redaction_service.create_stop_text(plan, stop, verified_facts_list_phase_1, verified_facts_list_phase_2, messages_history)
                self.registery.storage.save(Category.REDACTION, self.user_context, text, id = stop.numero)
                self.registery.storage.save(Category.REDACTION_HISTORY, self.user_context, messages_history, id = stop.numero)
                logger.info(f"Stop written : {stop.numero} - {stop.titre_etape}")
            
            content_list.stop.append(ContentStop(id = stop.numero, content = text))

        return content_list
    
    async def phonemes_detection(self, plan: AudioguidePlan, audioguide_text: AudioguideFinalText) -> PhonemesList:   
        phonemes_detection = PhonemDetection(self.user_context, self.registery)
        return await phonemes_detection.get_phonemes(plan, audioguide_text)

    async def audio_generation(self, phonemes_list: PhonemesList, audioguide_text: AudioguideFinalText):
        coroutine_list = []
        for stop in audioguide_text.stops:
            if self.registery.storage.does_exist(Category.AUDIO, self.user_context, id = stop.numero):
                logger.info(f"Audio already generated for stop {stop.numero}")
                continue

            # if stop.numero == 1:
            if True:
                coroutine_list.append(self._audio_single_stop(stop.content, stop, phonemes_list))
            logger.info(f"Audio generation for stop {stop.numero} - {stop.titre_etape} added to the queue!")

        await asyncio.gather(*coroutine_list)

        logger.info(f"All audio is now generated!")

    async def _audio_single_stop(self, content, stop, phonemes_list):
        try:
            audio, content_with_ssml = await self.audio_service.generate_audio(content, phonemes_list)
            self.registery.storage.save(Category.AUDIO, self.user_context, audio, id = stop.numero)
            self.registery.storage.save(Category.REDACTION_WITH_SSML, self.user_context, content_with_ssml, id = stop.numero)
            logger.info(f"Audio generated for stop {stop.numero} - {stop.titre_etape}")
        except Exception as e:
            logger.error(f"Error generating audio for stop {stop.numero}: {e}")
            

async def orchestrator(user_context: UserContext):
    registery = WorkerRegistry(
        search_worker=ExaSearch(),
        claude_worker=Claude(),
        storage=SaveFiles(),
        simulation_strategy=SimulationStrategy(),
        simulation_plan=SimulationPlan(),
        gemini_worker=Gemini(),
        azureTTS_worker=AzureTTS(),
        # simulation_content_prospector=SimulationContentProspector(),
    )

    # Load all the business classes
    audio_service = AudioService(user_context, registery, languages_no_phonemes_requiered=TTS_LANGUAGES_NO_PHONEMES)
    strategy_service = StrategyService(user_context, registery)
    plan_service = PlanService(user_context, registery)
    redaction_service = RedactionService(user_context, registery)
    

    orchestration = Orchestration(user_context, 
        registery,
        audio_service=audio_service,
        strategy_service=strategy_service,
        plan_service=plan_service,
        redaction_service=redaction_service,
        )


    logger.info("DEBUT DE LA STRATEGIE")
    strategy = await orchestration.strategy()
    logger.info("FIN DE LA STRATEGIE")

    logger.info("DEBUT DE LA RECHERCHE")
    verified_facts_list_phase_1 = await orchestration.research("phase_1", strategy)
    logger.info("FIN DE LA RECHERCHE")

    logger.info("DEBUT DU PLAN")
    plan = await orchestration.plan(strategy, verified_facts_list_phase_1)
    logger.info("FIN DU PLAN")

    logger.info("DEBUT PHASE RECHERCHE 2")
    verified_facts_list_phase_2 = await orchestration.research("phase_2", strategy, plan)
    logger.info("FIN PHASE RECHERCHE 2")

    logger.info("DEBUT DE LA REDACTION")
    audioguide_text = await orchestration.redaction(plan, verified_facts_list_phase_1, verified_facts_list_phase_2)
    logger.info("FIN DE LA REDACTION")

    logger.info("DEBUT DE LA GESTION DES PHONEMES")
    phonemes_list = await orchestration.phonemes_detection(plan, audioguide_text)
    logger.info("FIN DE LA GESTION DES PHONEMES")

    logger.info("DEBUT DE LA GENERATION DE l'AUDIO")
    await orchestration.audio_generation(phonemes, audioguide_text)
    logger.info("FIN DE LA GENERATION DE l'AUDIO")