
from loguru import logger
from string import Template
from typing import TYPE_CHECKING
from models.schemas import ResearchTopic, ResearchOutput, ResearchOutputLine
import asyncio

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry


class ContentProspector:
    def _init_(self, user_context: UserContext, registery : WorkerRegistry):
        self.user_context = user_context
        self.registery = registery

    async def content_prospector(self, research_topic: ResearchTopic, research_angle: str):
        """Generation of content, with high risk of hallucination, 0.6 temperature to have a good mix between creativity and fiability"""

        match research_topic.type:
            case "Lieu":
                with open("prompt/master_prompt_content_prospector_lieu.md", "r", encoding="utf-8") as f:
                    template_brut = Template(f.read())

            case "Theme":
                with open("prompt/master_prompt_content_prospector_theme.md", "r", encoding="utf-8") as f:
                    template_brut = Template(f.read())

            case "Deep_Dive":
                with open("prompt/master_prompt_content_prospector_deep_dive.md", "r", encoding="utf-8") as f:
                    template_brut = Template(f.read())

        prompt = template_brut.substitute(
            city_name=self.user_context.city,
            topic=research_topic.name,
            angle_narratif=research_angle
        )

        worker = self.registery.claude_worker

        logger.info(f"content_prospector | location={research_topic.name}")
        content = await asyncio.to_thread(worker.get_text, prompt, temperature=0.6)

        parsed_content = self._parse_content_prospector(content, research_topic)

    def _parse_content_prospector(self, text, research_topic: ResearchTopic):
        research_output = ResearchOutput(raw_output = text)

        # We get only the DSV part without the sources
        raw_content = text.split("===MASTER_INDEX===")[0]
        for line in (line for line in raw_content.strip().split("\n") if line.strip()): # a lot of lines are empty and should be removed
            try: 
                logger.debug(f"line : {line}")
                input = line.split("|")

                match research_topic.type:
                    case "Lieu" | "Theme":
                        # logger.debug(f"query list : {input[5]}")

                        # Exa requests are on the six columns for "lieu"
                        parsed_research_requests = input[5].split(";;")

                        research_output.research_topics.append(ResearchOutputLine(
                                    category=input[0],
                                    title=input[1],
                                    input=input[2], 
                                    visual_proof=input[3],
                                    confidence=input[4],
                                    queries=parsed_research_requests
                        ))
                    case "Deep_Dive":
                        parsed_research_requests = input[2].split(";;")
                        research_output.research_topics.append(ResearchOutputLine(
                                    input=input[0], 
                                    confidence=input[1],
                                    queries=parsed_research_requests
                            ))

            except Exception as e:
                logger.error(f"Cannot be parsed, line: {line} | {e}")

        logger.debug(f"research_output : {research_output}")
        return research_output 
