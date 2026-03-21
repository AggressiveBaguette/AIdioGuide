from dotenv import load_dotenv
load_dotenv('.env')

import time
from utils import extract_first_sentence

from google import genai
from loguru import logger
from utils import save_LLM_output




class Gemini:
    def __init__(self):
        self.client = genai.Client()
        self.text_model = "gemini-3-flash-preview"
        self.model_min_token_cache = 1024


    async def get_text(self, content, system_prompt="", research_block_1="", research_block_2="", plan="", temperature=1, cache_requested = False):
        # async http call, wait for the full text to be generated
        # temperature is not use anymore, based on Gemini 3 google guidelines, as gemini is only optimised for a temp of 1. 
        # 
        contents = [system_prompt, content]
        
        try:
            logger.info(f"Gemini call")            
            response = await self.client.aio.models.generate_content(
                model=self.text_model, contents=contents
            )
            logger.debug(f"response: {response}")
            logger.debug(f"contenu : {response.candidates[0].content.parts[0].text}")
            return response.candidates[0].content.parts[0].text
        except Exception as e:
            logger.error(f"[Error]: {e}")
            raise e

