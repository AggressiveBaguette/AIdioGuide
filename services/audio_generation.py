from loguru import logger
from models.schemas import Category
import re
from typing import TYPE_CHECKING
from config import TTS_LANGUAGES_NO_PHONEMES
import asyncio

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry


class AudioService:
    def __init__(self, userContext : UserContext,registery : WorkerRegistry):
        self.registery = registery
        self.user_context = userContext

    async def generate_audio(self, content, foreign_terms, is_simulation=False):
        if is_simulation:
            worker = self.registery.simulation_audio
        else:
            worker = self.registery.azureTTS_worker

        content = self._add_SSML_tags(content, foreign_terms)
        audio_content = await worker.get_audio(content, voice = self.user_context.language.voice_id)
        return audio_content

            
    def _add_SSML_tags(self, content, foreign_terms):
        # Note: foreign_terms need to be sorted witht the longuest epression first. It is normally done by the phonem_detection service.
        logger.debug(f"foreign_terms : {foreign_terms}")

        for term in foreign_terms.replacement_list:            
            pattern = rf"\b{re.escape(term.expression)}\b"
            
            #If TTS manage natively our language, then we use the native capcilities, otherwise we use the phonemes to have the right prononciation
            if term.langue in TTS_LANGUAGES_NO_PHONEMES:
                replacement = rf"<lang xml:lang='{term.langue}'>\g<0></lang>"
            else:
                replacement = rf"<phoneme alphabet='ipa' ph='{term.phonemes_ipa}'>\g<0></phoneme>"
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        return content
        