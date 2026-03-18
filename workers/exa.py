from exa_py import Exa
import os
import asyncio
import time
from loguru import logger


class ExaSearch:
    def __init__(self):
        self.api_key = os.getenv("EXA_API_KEY")
        self.lock = asyncio.Lock()
        self.last_call_time = 0
        # Exa rate limit is 10 requests per second, so we make sure there is at least 0.15 seconds between requests
        self.min_interval = 0.2

    async def search(self, query):
        # Rate limit management
        async with self.lock:
            elapsed = time.monotonic() - self.last_call_time
            delay = self.min_interval - elapsed
            if delay > 0:
                await asyncio.sleep(delay)
            self.last_call_time = time.monotonic()

        return await asyncio.to_thread(self._sync_search, query)

    def _sync_search(self, query):
        logger.debug(f"Exa query : {time.monotonic()} - {query}")
        exa = Exa(self.api_key)
        results = exa.search(
            query,
            type = "auto",
            output_schema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "trends": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "key_companies": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["summary", "trends"]
            },
            contents = {
                "highlights": {
                    "max_characters": 1000
                }            
            },
            num_results=5
        )

        clean_results = [
            {"title": r.title, "url": r.url, "highlights": r.highlights}
            for r in results.results
        ]

        logger.debug(f"Exa result : {clean_results}")

        return clean_results
