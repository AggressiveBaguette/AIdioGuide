from sre_constants import CATEGORY
import asyncio
from loguru import logger
from models.context import UserContext
from models.registry import WorkerRegistry
from models.schemas import Category, ResearchOutput, ResearchTopic, VerifiedResearchOutput, VerifiedResearchOutputConcatenated, VerifiedResearchOutputConcatenatedLine
from services.research.content_prospector import ContentProspector
from services.research.web_searches import WebSearches
from services.research.content_verifier import ContentVerifier

class ResearchOrchestrator:
    """Note: it is important to manage properly the different research phases to ensure good LLM cache utilisation"""

    def __init__(self, user_context: UserContext, registery: WorkerRegistry, phase):
        self.user_context = user_context
        self.registery = registery
        self.phase = phase

    async def get_research_results(self, research_topic: ResearchTopic , research_angle: str) -> VerifiedResearchOutput:
        """Prospection by a first LLM with high temperature
           Then, we perform research on the web to fact check it
           Lastly, a low temperature LLM removes hallucination or low quality data
        """
        self.content_prospector = ContentProspector(self.user_context, self.registery)
        self.web_searches = WebSearches(self.user_context, self.registery)
        self.content_verifier = ContentVerifier(self.user_context, self.registery)

        logger.info(f"get_research_results | topic={research_topic}")
        prospection = await self._content_prospector(research_topic, research_angle)
        logger.info(f"get_research_results | Content Prospector done | topic={research_topic}")   

        research_facts = await self._perform_web_searches(research_topic, prospection)
        logger.info(f"get_research_results | Web Searches done | topic={research_topic}")   

        verified_facts = await self._verify_content(research_topic, prospection, research_facts)        
        logger.info(f"get_research_results | verify content done | topic={research_topic}")   

        return verified_facts
 


    async def _content_prospector(self, research_topic: ResearchTopic, research_angle):
        """Generation of content, with high risk of hallucination, 0.6 temperature to have a good mix between creativity and fiability"""

        if self.registery.storage.does_exist_research(Category.PROSPECTOR, self.user_context, self.phase, research_topic.name):
            logger.info(f"content_prospector | research_topic={research_topic.name} already done")
            prospection = self.registery.storage.loads_research(Category.PROSPECTOR, self.user_context, self.phase, research_topic.name)
            parsed_prospection = self.content_prospector.parse_content_prospector(prospection, research_topic)            
            return parsed_prospection

        
        prospection = await self.content_prospector.content_prospector(research_topic, research_angle)
        self.registery.storage.save_research(
            category = Category.PROSPECTOR,
            user_context = self.user_context,
            content = prospection.raw_output,
            phase = self.phase,
            research_topic = research_topic.name,
            )
        return prospection

    async def _perform_web_searches(self, research_topic: ResearchTopic, prospection: ResearchOutput):
        """Perform research for the monument"""
        coroutine_search_list = []

        for entry in prospection.research_lines:
            logger.debug(f"entry: {entry}")
            for query in entry.queries:
                logger.debug(f"{query} : {query}")
                new_coroutine_search = self._perform_and_save_web_search(query, research_topic)
                coroutine_search_list.append(new_coroutine_search)
        logger.debug(f"coroutine_search_list: {len(coroutine_search_list)} items")

        web_searches_list = await asyncio.gather(*coroutine_search_list)
        errors = [r for r in web_searches_list if isinstance(r, Exception)]
        if errors:
            logger.error(f"{len(errors)} coroutines crashed! First error : {errors[0]}")

        # Create a single document with all researchs results for the given research topic
        research_facts = self.web_searches.format_all_web_searches(web_searches_list)
        self.registery.storage.save_research(Category.RESEARCH_CONCATENATED, self.user_context, research_facts, self.phase, research_topic.name)

        return research_facts
        

    async def _perform_and_save_web_search(self, query_name, research_topic: ResearchTopic):
        if self.registery.storage.does_exist_research(
            category = Category.RESEARCH,
            user_context = self.user_context, 
            phase = self.phase, 
            research_topic = research_topic.name,
            title = query_name
        ):
            logger.debug(f"research | research_topic={research_topic.name} - {query_name} already done")
            research_results = self.registery.storage.loads_research(Category.RESEARCH, self.user_context, self.phase, research_topic.name, query_name)
            return research_results

        try:
            logger.debug(f"research | research_topic={research_topic.name} - {query_name} not done")
            search_results = await self.web_searches.search(query_name)
            self.registery.storage.save_research(Category.RESEARCH, self.user_context, search_results, self.phase, research_topic.name, query_name)
            return search_results 
        except Exception as e:
            logger.error(f"Error searching for {query_name}: {e}")
            raise

    # async def _concatenate_research(self):
    #     """Concatenate all research results for the given research topic"""
    #     self.web_search_results = self.registery.storage.loads_all_research(Category.RESEARCH, self.user_context, self.phase, self.research_topic["name"])
    #     logger.debug(f"web_search_results : {len(self.web_search_results)} results")

    #     """Transform the json to DSV to save tokens"""
    #     concatenated_results = ""
    #     for queries_result in self.web_search_results:
    #         logger.debug(f"result : {queries_result}")
    #         for query in queries_result:
    #             logger.debug(f"query result : {query}")
    #             concatenated_results += f"{query['title']}|"
    #             concatenated_results += f"{query['url']}|"
    #             for result in query['highlights']:
    #                 concatenated_results += f"{result.replace('|', ';').replace('\n', ' ')}" # sanitize for futur parsing on |
    #             concatenated_results += "\n"

    #     self.registery.storage.save_research(Category.RESEARCH_CONCATENATED, self.user_context, concatenated_results, self.phase, self.research_topic["name"])
    #     logger.debug(f"concatenated_results : {concatenated_results[:200]}")
    #     self.research_facts = concatenated_results

    async def _verify_content(self, research_topic: ResearchTopic, prospection: ResearchOutput, research_facts: str):
        """Verify content for the monument"""
        if self.registery.storage.does_exist_research(Category.VERIFIED_RESEARCH, self.user_context, self.phase, research_topic.name):
            logger.info(f"VERIFIED_RESEARCH | research_topic={research_topic.name} already done")
            verified_claims = self.registery.storage.loads_research(Category.VERIFIED_RESEARCH, self.user_context, self.phase, research_topic.name)
            verified_claims = self.content_verifier.parse_verified_content(verified_claims, research_topic)
            return verified_claims
        else:

            try:
                verified_claims = await self.content_verifier.verify_content(research_topic=research_topic, prospection=prospection, research_facts=research_facts)
                self.registery.storage.save_research(
                    Category.VERIFIED_RESEARCH,
                    self.user_context,
                    verified_claims.raw_output,
                    self.phase,
                    research_topic.name)
            except Exception as e:
                logger.error(f"Error verifying content : {research_topic.name}: {e}")
                raise e
            
    def concatenate_verified_researches(self, verified_facts_list: list[VerifiedResearchOutput]) -> VerifiedResearchOutputConcatenated:
        # formating a DSV to send the research data to the LLM that is going to perform the planification. DSV is use instead of json to reduce the number of used tokens.
        raw_output_list = []
        research_lines_list = []
        id = 1
        
        for facts in verified_facts_list:
            block_list = []
            for fact in facts.research_lines:
                category = fact.category or ""
                visual_proof = fact.visual_proof or ""
                parts = [f"ID_id", category, fact.title, fact.affirmation, visual_proof, fact.confidence]
                block_list.append("|".join(parts))

                research_lines_list.append(VerifiedResearchOutputConcatenatedLine(
                    id = f"ID_{id}",
                    **fact.model_dump()
                ))

                id += 1
            raw_output_list.append("\n".join(block_list))
        logger.debug(f"concatenate_verified_researches : {raw_output_list}")

        verified_research_concatenated = VerifiedResearchOutputConcatenated(
            raw_output="\n----\n".join(raw_output_list),
            research_lines=research_lines_list
        )

        self.registery.storage.save_research(Category.RESEARCH_CONCATENATED, self.user_context, verified_research_concatenated.raw_output, phase=self.phase)
        return verified_research_concatenated





    



        
