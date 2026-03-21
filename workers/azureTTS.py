from loguru import logger
import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv
import asyncio


class AzureTTS:
    def __init__(self):
        api_key = os.getenv("AZURE_API_KEY")
        region=os.getenv("AZURE_REGION")
        self.config = speechsdk.SpeechConfig(subscription=api_key, region=region)


    async def get_audio(self, content, voice):
      try:
        logger.debug(f"Start AzureTTS")
        self.config.speech_synthesis_voice_name = voice
        self.config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3)

        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.config)

        future = speech_synthesizer.speak_ssml_async(content)
        result = await asyncio.to_thread(future.get)
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
          logger.debug(f"End AzureTTS")        
          return result.audio_data   
        else:
          logger.error(f"Azure TTS failed: {result.reason}. Details: {result.cancellation_details.error_details}")
          raise Exception(f"Azure TTS failed: {result.reason}. Details: {result.cancellation_details.error_details}")
      except Exception as e:
        if result and result.cancellation_details:
          logger.error(f"Azure TTS failed: {result.reason}. Details: {result.cancellation_details.error_details}")
        else:
          logger.error(f"Azure TTS failed: {e}")
        raise