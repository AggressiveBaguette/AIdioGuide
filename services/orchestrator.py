import asyncio
from string import Template
from loguru import logger
from models.context import UserContext
from models.registry import WorkerRegistry
from models.schemas import AudioguidePlan
from workers.exa import ExaSearch
from workers.claude import Claude
from workers.storage import SaveFiles
from workers.simulation import SimulationStrategy, SimulationPlan
from services.researcher import Research
from workers.gemini import Gemini
from services.phonemes_detection import PhonemDetection
from models.schemas import Category
from workers.azureTTS import AzureTTS
from services.audio_generation import AudioService
from config import TTS_LANGUAGES_NO_PHONEMES

class Orchestration:
    def __init__(self, user_context: UserContext, registery: WorkerRegistry, audio_service: AudioService):
        self.user_context = user_context
        self.registery = registery
        self.research_phases = {}
        self.audio_service = audio_service

        with open("prompt/master_prompt.txt", "r", encoding="utf-8") as f:
            template_brut = Template(f.read())

        self.system_prompt = template_brut.substitute(
            city=user_context.city,
            language=user_context.language.code
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
                language=self.user_context.language.code,
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
            return self.plan

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
            return self.plan

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

        for stop in self.plan.parcours:
            logger.debug(f"Stop : {stop}")

            # 
            # A REFACTO L'HISTORY FONCTIONNE PAS AVEC LE CHARGEMENT
            # 
            if self.registery.storage.does_exist(Category.REDACTION, self.user_context, id = stop.numero):
                logger.info(f"Redaction {stop.numero} - {stop.titre_etape} already created!")

            else:
                # DEBUT V2 AVEC MÉMOIRE
                facts_phase_1, facts_phase_2 = await self.get_facts(stop)

                logger.debug(f"Content : {system_prompt}")
                logger.debug(f"Stop name : {stop.numero} - {stop.titre_etape}")
                if is_simulation:
                    worker = self.registery.simulation_plan
                else:
                    worker = self.registery.claude_worker

                with open("prompt/prompt_instructions_redaction.md", "r", encoding="utf-8") as f:
                    template_brut = Template(f.read())
                prompt = template_brut.substitute(
                    nom_lieu = stop.localisation,
                    titre_etape = stop.titre_etape,
                    consigne_plume = stop.consigne_plume,
                    transition_vers_suivant = stop.transition_vers_suivant,
                    cible_duree_audio = stop.cible_duree_audio,
                    faits_bruts_phase_1 = facts_phase_1,
                    faits_bruts_phase_2 = facts_phase_2,
                )

                # if stop.titre_etape == "La Conciergerie : Quand le Palais Devient Cage":
                if True:
                    stop_text = worker.get_text(prompt, system_prompt=system_prompt, temperature = 0.8, cache = True, messages_history = messages_history)
                    self.registery.storage.save(Category.REDACTION, self.user_context, stop_text, id = stop.numero)
                    messages_history.append({"role": "assistant", "content": stop_text})

                # FIN V2 AVEC MÉMOIRE


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
                
    
    async def phonemes_detection(self, is_simulation = False):
        phonemes_detection = PhonemDetection(self.user_context, self.registery, self.plan)
        return await phonemes_detection.get_phonemes(is_simulation)

    async def audio_generation(self, foreign_terms, plan, is_simulation=False):
        coroutine_list = []
        for stop in plan.parcours:
            if self.registery.storage.does_exist(Category.AUDIO, self.user_context, id = stop.numero):
                logger.info(f"Audio already generated for stop {stop.numero}")
                continue

            content = self.registery.storage.loads(Category.REDACTION, self.user_context, id = stop.numero)
            # if stop.numero == 1:
            if True:
                coroutine_list.append(self._audio_single_stop(content, stop, foreign_terms, is_simulation))
            logger.info(f"Audio generation for stop {stop.numero} - {stop.titre_etape} added to the queue!")

        await asyncio.gather(*coroutine_list)

        logger.info(f"Audio generation completed!")

    async def _audio_single_stop(self, content, stop, foreign_terms, is_simulation=False):
        try:
            audio, content = await self.audio_service.generate_audio(content, foreign_terms, is_simulation)
            self.registery.storage.save(Category.AUDIO, self.user_context, audio, id = stop.numero)
            self.registery.storage.save(Category.REDACTION_WITH_SSML, self.user_context, content, id = stop.numero)
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

    orchestration = Orchestration(user_context, registery, audio_service=audio_service)


    logger.info("DEBUT DE LA STRATEGIE")
    await orchestration.strategy_agent(is_simulation=False)
    logger.info("FIN DE LA STRATEGIE")

    logger.info("DEBUT DE LA RECHERCHE")
    await orchestration.research("phase_1", is_simulation=False)
    logger.info("FIN DE LA RECHERCHE")

    logger.info("DEBUT DU PLAN")
    plan = await orchestration.plan(is_simulation=False)
    logger.info("FIN DU PLAN")

    logger.info("DEBUT PHASE RECHERCHE 2")
    await orchestration.research("phase_2", is_simulation=False)
    logger.info("FIN PHASE RECHERCHE 2")

    logger.info("DEBUT DE LA REDACTION")
    await orchestration.redaction(is_simulation=False)
    logger.info("FIN DE LA REDACTION")

    logger.info("DEBUT DE LA GESTION DES PHONEMES")
    phonemes = await orchestration.phonemes_detection(is_simulation=False)
    logger.info("FIN DE LA GESTION DES PHONEMES")

    logger.info("DEBUT DE LA GENERATION DE l'AUDIO")
    await orchestration.audio_generation(phonemes, plan, is_simulation=False)
    logger.info("FIN DE LA GENERATION DE l'AUDIO")