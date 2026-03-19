from loguru import logger
from typing import TYPE_CHECKING
from string import Template
import asyncio
from models.schemas import ResearchOutput, ResearchTopic, VerifiedResearchOutput, VerifiedResearchOutputLine, ResearchOutputLinePhase2, ResearchOutputLinePhase1

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry

class ContentVerifier:
    def __init__(self, user_context: UserContext, registery: WorkerRegistry):
        self.user_context = user_context
        self.registery = registery  


    async def verify_content(self, research_topic: ResearchTopic, prospection: ResearchOutput, research_facts: str):
        """Verify content for the monument"""
        logger.debug(f"Verify content started: {research_topic.name}")
        worker = self.registery.gemini_worker
        
        with open("prompt/master_prompt_fact_checker.md", "r", encoding="utf-8") as f:
            template_brut = Template(f.read())
        system_prompt = template_brut.substitute(
            city_name=self.user_context.city,
            monument=research_topic.name
        )

        # We remove the exa queries of the paylod to save some token. They do not need to be verified
        prospection_without_search_requests = self._remove_search_requests(prospection)

        # We build the content that will be sent for verification
        fragments = []
        fragments.append("## CLAIMS \n\n")
        fragments.append(prospection_without_search_requests)
        fragments.append("\n\n## CONTEXTE DE RECHERCHE \n\n")
        fragments.append(research_facts)
        content = "".join(fragments)

        verified_claims = await asyncio.to_thread(worker.get_text(content=content, system_prompt=system_prompt, temperature = 0))
        logger.debug(f"verified_claims {research_topic.name}: {verified_claims}")
        
        parsed_verified_claims = self.parse_verified_content(verified_claims, research_topic)
        return parsed_verified_claims


    # def _remove_search_requests(self, raw_content: str):
    #     """we remove the last column of each line"""
    #     content = raw_content.splitlines()
    #     new_line_list = []

    #     lines = (line for line in content if line.strip())
    #     for line in lines:
    #         # exa query are in the last colum, so they need to be removed
    #         if '|' in line:
    #             search_claims = line.rsplit('|', 1)
    #             new_line_list.append(search_claims[0].strip())
    #         else:
    #             logger.warning(f"Search claim not formatted properly: {line}")

        
    #     new_content = "\n".join(new_line_list)
    #     logger.debug(f"new_content : {new_content}")
    #     return new_content

    def _format_claims_to_be_verified(self, prospection: ResearchOutput):
        """A DSV is prepared with only the facts that are needed for the LLM to perfrom the verification. We don't send everything to save tokens """

        output_list = []

        for line in prospection.research_lines:
            # Queries need to be removed as they are not needed for the verification
            if isinstance(line, ResearchOutputLinePhase1):
                parts = [
                    line.category,
                    line.title,
                    line.affirmation,
                    line.visual_proof,
                    line.confidence,
                ]
            elif isinstance(line, ResearchOutputLinePhase2):
                parts = [
                    line.affirmation,
                    line.confidence,
                ]
            output_list.append("|".join(parts))
        return "\n".join(output_list)
        

    def parse_verified_content(self, text, research_topic: ResearchTopic):
        research_output = VerifiedResearchOutput(raw_output = text)

        lines = (line for line in text.splitlines() if line.strip())
        for line in lines:
            parts = [c.strip() for c in line.split("|")]

            try: 
                # Output format is different between research phase 1 (lieu & theme) and phase 2 (deep dive)
                match research_topic.type:
                    case "Lieu" | "Theme":
                        research_output.research_lines.append(VerifiedResearchOutputLine(
                            category = parts[0],
                            title = parts[1],
                            affirmation = parts[2],
                            visual_proof = parts[3],
                            confidence = parts[4],
                        ))
                    case "Deep_Dive":
                        research_output.research_lines.append(VerifiedResearchOutputLine(
                            # we need to add a title for filtering later in the workflow, as we only need to send relevant researches to our redaction.
                            title = research_topic.name,
                            affirmation = parts[0],
                            confidence = parts[1],
                        ))
            except Exception as e:
                logger.error(f"Cannot be parsed, line: {line} | {e}")

        logger.debug(f"research_output : {research_output}")
        return research_output


            

        
