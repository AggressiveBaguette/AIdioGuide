
from loguru import logger
from string import Template
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry


class StrategyService:
    def __init__(self, user_context: UserContext, registery : WorkerRegistry):
        self.user_context = user_context
        self.registery = registery

    def define_strategy(self):
        with open("prompt/master_prompt_strategy.md", "r", encoding="utf-8") as f:
            template_brut = Template(f.read())
        content = template_brut.substitute(
            city_name=self.user_context.city,
            language=self.user_context.language.code,
            user_profile=self.user_context.comment
        )
        logger.debug(f"content : {content}")
        worker = self.registery.claude_worker

        strategy = worker.get_text(content = content, temperature = 1)
        logger.debug(f"Strategy : {strategy}")
        return strategy

    