
from models.schemas import ResearchTopic
from loguru import logger
from string import Template
from typing import TYPE_CHECKING
from models.schemas import Strategy, ResearchTopic

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry


class StrategyService:
    def __init__(self, user_context: UserContext, registery : WorkerRegistry):
        self.user_context = user_context
        self.registery = registery

    async def define_strategy(self):
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
        parsed_strategy = self.parse_strategy(strategy)
        logger.debug(f"Strategy : {strategy}")
        return parsed_strategy

    def parse_strategy(self, raw_output):
        result = Strategy(raw_output=raw_output)

        strategy_line = raw_output.strip().split("\n")

        for line in strategy_line:
            logger.debug(f"line : {line}")
            parts = line.strip().split("|")
            match parts[0]:
                case "STRATEGIE" if len(parts) >= 2:
                    result.strategy_thinking = parts[1]
                case "ANGLE_RECHERCHE" if len(parts) >= 2:
                    result.research_angle = parts[1]
                case "Lieu" | "Theme" if len(parts) >= 3:
                    result.research_topics.append(ResearchTopic(
                        type=parts[0],
                        name=parts[1],
                        angle=parts[2]
                    ))
                case _:
                    logger.warning(f"Line cannot be parsed : {line}")
                    
        return result

    