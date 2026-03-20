import os
from anthropic import AsyncAnthropic, RateLimitError
from utils import save_LLM_output
import re
from loguru import logger
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type

class Claude:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = AsyncAnthropic(api_key=self.api_key)

    def get_system_block(self, system_prompt="", research_block_1="", research_block_2="", plan=""):
        """The order of the different blocks is thought to optimize token usage, using the cache strategy"""

        system_block = []

        if system_prompt:
            system_block.append({
                    "type": "text",
                    "text": system_prompt
                })

        if research_block_1:
            system_block.append({
                    "type": "text",
                    "text": research_block_1,
                    # "cache_control": {"type": "ephemeral"}
                })

        if research_block_2:
            system_block.append({
                "type": "text",
                "text": research_block_2,
                # "cache_control": {"type": "ephemeral"}
            })

        if plan:
            system_block.append({
                "type": "text",
                "text": plan,
                # "cache_control": {"type": "ephemeral"}
            })

        return system_block


    async def get_json(self, pydantic_schema, content, system_prompt="", research_block_1="", research_block_2="", plan="", temperature=1):
        # async http call, return json matching pydantic classes
        claude_response = await self.get_text(content, system_prompt, research_block_1, research_block_2, plan, temperature)

        logger.debug("get_json")
        
        # Delete markdown json claude often sends at the beginning of its response...
        match = re.search(r"```json\s*(.*?)\s*```", claude_response, re.DOTALL)
        # First group is the json markdown, so we select the second
        json_str = match.group(1).strip() if match else claude_response.strip()

        try:
            validated_data = pydantic_schema.parse_raw(json_str)
            return validated_data

        except Exception as e:
            logger.error(f"Claude response : {claude_response}")
            save_LLM_output(claude_response, "Claude_Sonnet_4_6")
            logger.error(f"[Error]: {e}")
            raise e

    @retry(
        wait=wait_random_exponential(min=1, max=60), 
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def get_text(self, content, system_prompt="", research_block_1="", research_block_2="", plan="", temperature=1, cache = False, messages_history: list | None = None):
        # async http call, wait for the full text to be generated
        try:
            logger.info("Before Claude API call")

            system_block = self.get_system_block(system_prompt, research_block_1, research_block_2, plan)
            # save_LLM_output(system_block, "System_block")

            # logger.debug(f"content : {content}")
            if messages_history is None:
                messages_history = []
            messages_history.append({"role": "user", "content": content})

            api_param = {
                "max_tokens": 16384,
                "system": system_block,
                "temperature": temperature,
                "messages": messages_history,
                "model": "claude-sonnet-4-6",
            }
            if cache:
                api_param["cache_control"] = {"type": "ephemeral"}

            logger.debug(f"Claude system_block : {system_block}")
            logger.debug(f"Claude messages_history : {messages_history[:100]}")
            response = await self.client.messages.create(**api_param)
            logger.info("Claude API call done")
            logger.debug(response)

            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude [Error]: {e}")
            raise