from sre_constants import CATEGORY
import asyncio
from string import Template
from loguru import logger
from models.context import UserContext
from models.registry import WorkerRegistry
from models.schemas import Category
from services.research.content_prospector import ContentProspector
from services.research.web_searches import WebSearches

class ResearchOrchestrator:
    """Note: it is important to manage properly the different research phases to ensure good LLM cache utilisation"""

    def __init__(self, user_context: UserContext, registery: WorkerRegistry):
        self.user_context = user_context
        self.registery = registery

    async def get_research_results(self, phase, research_topic, research_angle):
        """Prospection by a first LLM with high temperature
           Then, we perform research on the web to fact check it
           Lastly, a low temperature LLM removes hallucination or low quality data
        """
        self.content_prospector = ContentProspector(self.user_context, self.registery)
        self.web_searches = WebSearches(self.user_context, self.registery)

        logger.info(f"get_research_results | topic={research_topic}")
        await self._content_prospector(phase, research_topic, research_angle)
        logger.info(f"get_research_results | Content Prospector done | topic={research_topic}")   

        await self._perform_web_searches()
        # logger.debug(f"web_search_results : {self.web_search_results}")
        logger.info(f"get_research_results | Web Searches done | topic={research_topic}")   

        await self._verify_content()        
        logger.info(f"get_research_results | verify content done | topic={research_topic}")   

 


    async def _content_prospector(self, phase, research_topic, research_angle):
        """Generation of content, with high risk of hallucination, 0.6 temperature to have a good mix between creativity and fiability"""

        if self.registery.storage.does_exist_research(Category.PROSPECTOR, self.user_context, phase, research_topic.name):
            logger.info(f"content_prospector | research_topic={research_topic.name} already done")
            prospection = self.registery.storage.loads_research(Category.PROSPECTOR, self.user_context, phase, research_topic.name)
            parsed_prospection = self.content_prospector.parse_content_prospector(prospection, research_topic)            
            return parsed_prospection

        
        prospection = await self.content_prospector.content_prospector(research_topic, research_angle)
        self.registery.storage.save_research(
            category = Category.PROSPECTOR,
            user_context = self.user_context,
            content = prospection.raw_output,
            phase = phase,
            research_topic = research_topic.name,
            )
        return prospection

    async def _perform_web_searches(self, is_simulation):
        """Perform research for the monument"""
        coroutine_search_list = []

        for entry in self.prospection:
            logger.debug(f"entry: {entry}")
            for query in entry["queries"]:
                logger.debug(f"{query} : {query}")
                new_coroutine_search = self._perform_and_save_search(query)
                coroutine_search_list.append(new_coroutine_search)

        await asyncio.gather(*coroutine_search_list, return_exceptions=True)

        # Create a single document with all researchs results for the given research topic
        # await self._concatenate_research()
        research_facts = self.web_searches.format_all_web_searches(coroutine_search_list)
        self.registery.storage.save_research(Category.RESEARCH_CONCATENATED, self.user_context, research_facts, self.phase, self.research_topic["name"])

        

    async def _perform_and_save_search(self, query_name):
        if self.registery.storage.does_exist_research(
                category = Category.RESEARCH,
                user_context = self.user_context, 
                phase = self.phase, 
                research_topic = self.research_topic.name,
                title = query_name
                ):

            logger.debug(f"research | research_topic={self.research_topic.name} - {query_name} already done")
            research_results = self.registery.storage.loads_research(Category.RESEARCH, self.user_context, self.phase, self.research_topic.name, query_name)
            return research_results

        try:
            search_results = await self.web_searches.search(query_name)
            self.registery.storage.save_research(Category.RESEARCH, self.user_context, search_results, self.phase, self.research_topic.name, query_name)
            return search_results 
        except Exception as e:
            logger.error(f"Error searching for {query_name}: {e}")

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

    async def _verify_content(self, is_simulation):
        """Verify content for the monument"""
        if self.registery.storage.does_exist_research(Category.VERIFIED_RESEARCH, self.user_context, self.phase, self.research_topic["name"]):
            logger.info(f"VERIFIED_RESEARCH | research_topic={self.research_topic["name"]} already done")
        else:

            try:

                if is_simulation:
                    worker = self.registery.simulation_content_verifier
                else:
                    worker = self.registery.gemini_worker
                
                with open("prompt/master_prompt_fact_checker.md", "r", encoding="utf-8") as f:
                    template_brut = Template(f.read())
                system_prompt = template_brut.substitute(
                    city_name=self.user_context.city,
                    monument=self.research_topic["name"]
                )

                prospection = self.registery.storage.loads_research(Category.PROSPECTOR, self.user_context, self.phase, self.research_topic["name"])
                # We remove the exa queries of the paylod to save some token. They do not need to be verified
                prospection_without_search_requests = self._remove_search_requests(prospection)

                # We build the content that will be sent for verification
                fragments = []
                fragments.append("## CLAIMS \n\n")
                fragments.append(prospection_without_search_requests)
                fragments.append("\n\n## CONTEXTE DE RECHERCHE \n\n")
                fragments.append(self.research_facts)
                content = "".join(fragments)

                verified_claims = worker.get_text(content=content, system_prompt=system_prompt, temperature = 0) 
                logger.debug(f"verified_claims {self.research_topic['name']}: {verified_claims}")

                if self.phase == "phase_2":
                    # We need to add the request name in phase_2 as a key, otherwise we won't be able to determine which claims is needed for which stop.
                    # phase 2 content is a little different than phase 1. Phase 1 is needed as a whole to determine the plan and ID are only managed later, after the plan is done. While pahse 2 is only aimed at a single stop.
                    verified_claims = "\n".join(f"{self.research_topic['name']}|{line}" for line in verified_claims.split("\n"))
                    logger.debug(f"verified_claims {self.research_topic['name']}: {verified_claims}")

                self.registery.storage.save_research(
                    Category.VERIFIED_RESEARCH,
                    self.user_context,
                    verified_claims,
                    self.phase,
                    self.research_topic["name"])
            except Exception as e:
                logger.error(f"Error verifying content : {self.research_topic['name']}: {e}")
            

    def _remove_search_requests(self, raw_content):
        """we remove the last column of each line"""
        content = raw_content.strip().split("\n")
        new_line_list = []

        for line in content:
            # exa query are in the last colum, so they need to be removed
            if not line:
                continue
            input = line.strip().rsplit('|', 1)
            new_line_list.append(input[0])

        
        new_content = "\n".join(new_line_list)
        logger.debug(f"new_content : {new_content}")
        return new_content

        



    



        
