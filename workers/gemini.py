from dotenv import load_dotenv
load_dotenv('.env')

import asyncio
import time
from utils import extract_first_sentence

from google import genai
from google.genai import types
from loguru import logger




class Gemini:
    def __init__(self):
        self.client = genai.Client()
        self.text_model = "gemini-3-flash-preview"
        self.model_min_token_cache = 1024


    def get_text(self, content, system_prompt="", research_block_1="", research_block_2="", plan="", temperature=1, cache_requested = False):
        # synchronous http call, wait for the full text to be generated

        contents = [system_prompt, content]

        try:
            logger.info(f"Gemini call")            
            response = self.client.models.generate_content(
                model=self.text_model, contents=contents
            )
            logger.debug(f"response: {response}")
            logger.debug(f"contenu : {response.candidates[0].content.parts[0].text}")
            return response.candidates[0].content.parts[0].text
        except Exception as e:
            logger.error(f"[Error]: {e}")
            if response:
                save_LLM_output(response, "Gemini Flash 3.0")
            raise e

    async def stream(self):
        sentence_extracted = None

        # stream answer from llm
        response_stream = self.client.aio.models.generate_content_stream(
            model=self.text_model, 
            contents=self.content,
        )

        sentence_buffer = ""

        start = time.perf_counter()
        async for chunk in response_stream:
            text_part = chunk.text
            sentence_buffer += text_part
            end = time.perf_counter()

            # print(f"chunk - {end - start}: {text_part}\n", end="", flush=True)
            # print(text_part)

            sentence_buffer, sentence_extracted = extract_first_sentence(sentence_buffer)

            if sentence_extracted:
                self.queue.put_nowait(sentence_extracted)


