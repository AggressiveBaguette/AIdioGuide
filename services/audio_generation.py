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
    def __init__(self, userContext : UserContext,registery : WorkerRegistry, languages_no_phonemes_requiered=None):
        self.registery = registery
        self.user_context = userContext
        self.languages_no_phonemes_requiered = languages_no_phonemes_requiered

    async def generate_audio(self, content, phonemes_replacement, is_simulation=False):
        if is_simulation:
            worker = self.registery.simulation_audio
        else:
            worker = self.registery.azureTTS_worker

        content = self._add_phonemes_foreign_tags(content, phonemes_replacement)
        content = self._add_phonemes_native_tags(content, phonemes_replacement)
        content = self._add_header_footer_tags(content)
        content = self._remove_useless_linebreak(content)
        audio_content = await worker.get_audio(content, voice = self.user_context.language.voice_id)
        return audio_content, content

            
    def _add_phonemes_foreign_tags(self, content, phonemes_replacement):
        # Note: phonemes_replacement need to be sorted witht the longuest epression first. It is normally done by the phonemes_detection service.
        logger.debug(f"phonemes_replacement : {phonemes_replacement}")

        for term in phonemes_replacement.replacement_list:
            if term.type == "foreign_entity":
                pattern = rf"\b{re.escape(term.expression)}\b"
            

                #If TTS manage natively our language, then we use the native capcilities, otherwise we use the phonemes to have the right prononciation
                if term.langue in self.languages_no_phonemes_requiered:
                    replacement = rf"<lang xml:lang='{term.langue}'>\g<0></lang>"
                else:
                    replacement = rf"<phoneme alphabet='ipa' ph='{term.phonemes_ipa}'>\g<0></phoneme>"
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        return content
        
    def _add_header_footer_tags(self, content):
        header = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="{self.user_context.language.code}"><voice name="{self.user_context.language.voice_id}">"""
        footer = "</voice></speak>"
        return header + content + footer
    
    def _add_phonemes_native_tags(self, content, phonemes_replacement):
        # Transform some nums hard to prononce by TTS like Louis XIV or François I by the phonem

        for term in phonemes_replacement.replacement_list:
            if term.type == "native_anomaly":
                pattern = rf"\b{re.escape(term.expression)}\b"

                #We force the phonemes to have the right prononciation
                replacement = rf"<phoneme alphabet='ipa' ph='{term.phonemes_ipa}'>\g<0></phoneme>"
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)            
        return content

    def _remove_useless_linebreak(self, content):
        # Remove lines break, to avoid TTS to make long pauses. Pauses are control through SSML tags.
        content = re.sub(r"\n", " ", content)
        return content