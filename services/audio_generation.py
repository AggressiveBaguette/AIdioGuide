from loguru import logger
from models.schemas import PhonemesList
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

    async def generate_audio(self, content: str, phonemes_replacement: PhonemesList) -> tuple[bytes, str]:
        worker = self.registery.azureTTS_worker

        content = self._add_header_footer_tags(content)
        content = self._remove_useless_linebreak(content)
        try:
            content_with_phonemes = self._add_phonemes_foreign_tags(content, phonemes_replacement)
            content_with_phonemes = self._add_phonemes_native_tags(content_with_phonemes, phonemes_replacement)

            audio_content = await worker.get_audio(content_with_phonemes, voice = self.user_context.language.voice_id)
            return audio_content, content
        except Exception as e:
            error_msg = str(e)
            if "1007" in error_msg:
                # Issue is with phonemes, we try to generate the audio without them
                content_without_phonemes = self._add_foreign_tags_but_no_phonemes(content, phonemes_replacement)
                audio_content = await worker.get_audio(content_without_phonemes, voice = self.user_context.language.voice_id)
                return audio_content, content_without_phonemes
            else:
                logger.error(f"Error generating audio: {e}")
                raise

            
    def _add_phonemes_foreign_tags(self, content: str, phonemes_replacement: PhonemesList) -> str:
        # Note: phonemes_replacement need to be sorted witht the longuest epression first. It is normally done by the phonemes_detection service.
        logger.debug(f"phonemes_replacement : {phonemes_replacement}")

        for term in phonemes_replacement.replacement_list:
            if term.type == "foreign_entity":
                pattern = rf"\b{re.escape(term.expression)}\b"
            

                #If TTS manage natively our language, then we use the native capabilities, otherwise we use the phonemes to have the right prononciation
                if term.langue in self.languages_no_phonemes_requiered:
                    replacement = rf"<lang xml:lang='{term.langue}'>\g<0></lang>"
                else:
                    replacement = rf"<phoneme alphabet='ipa' ph='{term.phonemes_ipa}'>\g<0></phoneme>"
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        return content
        
    def _add_header_footer_tags(self, content: str) -> str:
        header = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="{self.user_context.language.code}"><voice name="{self.user_context.language.voice_id}">"""
        footer = "</voice></speak>"
        return header + content + footer
    
    def _add_phonemes_native_tags(self, content: str, phonemes_replacement: PhonemesList) -> str:
        # Transforms some names hard to pronounce by a TTS like Louis XIV or François I by their given phonem

        for term in phonemes_replacement.replacement_list:
            if term.type == "native_anomaly":
                pattern = rf"\b{re.escape(term.expression)}\b"

                #We force the phonemes to have the right prononciation
                replacement = rf"<phoneme alphabet='ipa' ph='{term.phonemes_ipa}'>\g<0></phoneme>"
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)            
        return content

    def _remove_useless_linebreak(self, content: str) -> str:
        # Remove lines break, to avoid TTS to make long pauses. Pauses are control through SSML tags.
        content = re.sub(r"\n", " ", content)
        return content

    def _add_foreign_tags_but_no_phonemes(self, content: str, phonemes_replacement: PhonemesList) -> str:
        # Note: phonemes_replacement need to be sorted witht the longuest epression first. It is normally done by the phonemes_detection service.
        logger.debug(f"phonemes_replacement : {phonemes_replacement}")

        for term in phonemes_replacement.replacement_list:
            if term.type == "foreign_entity":
                pattern = rf"\b{re.escape(term.expression)}\b"
            
                #We do not put the phonemes in this case, it is here to handle bad phonemes generation by the LLM and phonemes not managed by the TTS
                if term.langue in self.languages_no_phonemes_requiered:
                    replacement = rf"<lang xml:lang='{term.langue}'>\g<0></lang>"
                    content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        return content