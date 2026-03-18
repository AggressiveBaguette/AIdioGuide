from models.schemas import Category, PhonemesList
from string import Template
from loguru import logger
from utils import parse_LLM_output
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry


class PhonemDetection:
    def __init__(self, user_context: UserContext, registery: WorkerRegistry, plan):
        self.user_context = user_context
        self.registery = registery
        self.plan = plan

    async def get_phonemes(self, text: str):
        if self.registery.storage.does_exist(Category.PHONEMES, self.user_context):
            logger.info(f"Phonemes already created!")
            return self.registery.storage.loads(Category.PHONEMES, self.user_context, pydantic_model = PhonemesList)
        else:
            text = await self._get_all_redaction()
            with open("prompt/master_prompt_linguist.md", "r", encoding="utf-8") as f:
                template_brut = Template(f.read())
            content = template_brut.substitute(
                city_name=self.user_context.city,
                language=self.user_context.language.code,
                texte_audio=text
            )
            logger.debug(f"content : {content[:10000]}")

            phonemes = self.registery.gemini_worker.get_text(content=content, temperature=0.1)

            logger.debug(f"phonemes : {phonemes}")

            parsed_phonemes = parse_LLM_output(phonemes, PhonemesList)
            # Phonemes need to be sorted from largest to smallest to be sure parts of long phonems are not replaced partially. E.g.: "Paris" is replaced first, so "Paris Match" cannot be replaced.
        
            parsed_phonemes.replacement_list.sort(key = lambda x: len(x.expression) if x.expression else 0, reverse = True)
            self.registery.storage.save(Category.PHONEMES, self.user_context, parsed_phonemes)
            logger.info(f"Phonemes created!")
            return parsed_phonemes

    async def _get_all_redaction(self):
        redaction = []
        for i in self.plan.parcours:
            redaction.append(self.registery.storage.loads(Category.REDACTION, self.user_context, id = i.numero))
        text = "\n---\n".join(redaction)
        logger.debug(f"text : {text[:500]}")
        return text

            