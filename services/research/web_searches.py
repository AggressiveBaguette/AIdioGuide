from loguru import logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry

class WebSearches:
    def __init__(self, user_context: UserContext, registry : WorkerRegistry):
        self.user_context = user_context
        self.registry = registry
    
    async def search(self, query_name):
        web_search_result = await self.registry.search_worker.search(query_name)
        return web_search_result 

    def format_all_web_searches(self, web_searches_list):
        logger.debug(f"web_search_results : {len(web_searches_list)} results")

        """Transform the json into a DSV file with | as column separator and \n as line separator  to save tokens"""
        concatenated_results = ""
        for queries_result in web_searches_list:
            logger.debug(f"result : {queries_result}")
            for query in queries_result:
                logger.debug(f"query result : {query}")
                concatenated_results += f"{query['title']}|"
                concatenated_results += f"{query['url']}|"
                for result in query['highlights']:
                    concatenated_results += f"{result.replace('|', ';').replace('\n', ' ')}" # sanitize for futur parsing on |
                concatenated_results += "\n"

        logger.debug(f"concatenated_results : {concatenated_results[:200]}")
        return concatenated_results.strip()

    
