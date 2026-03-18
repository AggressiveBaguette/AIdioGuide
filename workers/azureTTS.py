from loguru import logger
import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv
import asyncio

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registery import WorkerRegistry
    from models.schemas import Category



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


# '''
#   For more samples please visit https://github.com/Azure-Samples/cognitive-services-speech-sdk 
# '''


# # Creates an instance of a speech config with specified subscription key and service region.

if __name__ == "__main__":
  # Note: the voice setting will not overwrite the voice element in input SSML.
  load_dotenv()
  api_key = os.getenv("AZURE_API_KEY")
  region=os.getenv("AZURE_REGION")
  print(f"region : {region}")

  config = speechsdk.SpeechConfig(subscription=api_key, region=region)
  config.speech_synthesis_voice_name = "fr-FR-Vivienne:DragonHDLatestNeural"

  # # text = """
  # # <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
  # #   <voice name="en-US-JennyMultilingualNeural">
  # #     The morning light was soft and the air unusually still. She walked through the empty streets, wondering where the day would take her.
  # #     <break time="500ms"/>
  # #     Last summer, we drove from <lang xml:lang='fr-FR'>Aix-en-Provence</lang> to <lang xml:lang='fr-FR'>Saint-Rémy-de-Provence</lang>, stopping at the <lang xml:lang='fr-FR'>Château de Roussan</lang> along the way. 
  # #     The chef, <lang xml:lang='fr-FR'>Jean-Pierre Beaumont</lang>, had trained at the <lang xml:lang='fr-FR'>École Hôtelière de Lausanne</lang> before opening his brasserie near the <lang xml:lang='fr-FR'>Place de la République</lang>.
  # #   </voice>
  # # </speak>
  # # """            

  # text = """
  # <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="fr-FR">
  #   <voice name="fr-FR-VivienneMultilingualNeural">
  #     La soirée était d'un ennui mortel jusqu'à ce que les invités n'arrivent enfin. 
  #     <break time="400ms"/>
  #     Le premier à entrer fut <lang xml:lang='en-GB'>Sir Alistair Thorne</lang>. Il arrivait tout droit de <lang xml:lang='en-GB'>Buckinghamshire</lang> et ne jurait que par son thé de chez <lang xml:lang='en-GB'>Fortnum &amp; Mason</lang>. 
  #     <break time="300ms"/>
  #     Il était accompagné de la volcanique <lang xml:lang='it-IT'>Alessandra Monteverdi</lang>, une sculptrice originaire de <lang xml:lang='it-IT'>Firenze</lang>. 
  #     Elle a passé la moitié de la nuit à hurler sur le pauvre <lang xml:lang='it-IT'>Lorenzo Ricci</lang> à propos d'une sombre histoire de <lang xml:lang='it-IT'>Fettuccine Alfredo</lang> mal cuites. 
  #     <break time="500ms"/>
  #     Franchement, quel bordel cosmopolite.
  #   </voice>
  # </speak>
  # """

  # # text = """
  # # <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="fr-FR">
  # #   <voice name="fr-FR-VivienneMultilingualNeural">
  # #     La soirée était d'un ennui mortel. 
  # #     <break time="400ms"/>
  # #     Le premier à entrer fut Sir Alistair <lang xml:lang='en-GB'><phoneme alphabet="ipa" ph="θɔːn">Thorne</phoneme></lang> ou <lang xml:lang='en-GB'>Thorne</lang>. 
  # #     Il arrivait de <lang xml:lang='en-GB'><phoneme alphabet="ipa" ph="ˈbʌkɪŋəmʃə">Buckinghamshire</phoneme></lang> ou <lang xml:lang='en-GB'>Buckinghamshire</lang> et ne jurait que par son thé.
  # #     <break time="300ms"/>
  # #     Il était avec <lang xml:lang='it-IT'>Alessandra Monteverdi</lang> et ce pauvre <lang xml:lang='it-IT'>Lorenzo Ricci</lang>. 
  # #     Elle hurlait encore à propos de ses <lang xml:lang='it-IT'>Fettuccine</lang> mal cuites. 
  # #     <break time="500ms"/>
  # #     Franchement, quel bordel cosmopolite.
  # #   </voice>
  # # </speak>"""


  text = """
  <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="fr-FR">
    <voice name="fr-FR-Vivienne:DragonHDLatestNeural">
    Le vieux châtelain, Monsieur Lefebvre, avait quitté Chamonix pour rejoindre le duc de La Rochefoucauld du côté de Cassis. C'était un voyage absurde. En chemin, il fit escale à Ploumanac'h, où il mangea des haricots devant le prieuré, observant les poules du couvent qui couvent silencieusement.
      
      La situation dégénéra quand son rival, un certain <lang xml:lang="es-ES">Juan-Pablo de la Cruz</lang>, débarqua d'un vol en provenance du <lang xml:lang="de-DE">Schwarzwald</lang>. L'imbécile prétendait avoir retrouvé les fameux héros de la région, mais il s'était juste bourré la gueule au Cointreau. 
      
      Finalement, Madame de Staël, excédée, les envoya tous chier à Bruxelles.  </voice>
  </speak>
  """
  # use the default speaker as audio output.
  config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3)
  audio_config = speechsdk.audio.AudioConfig(filename="test.mp3")
  speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=audio_config)

  # result = speech_synthesizer.speak_text_async(text).get()
  result = speech_synthesizer.speak_ssml_async(text).get()
  # Check result
  if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
      print("Speech synthesized for text [{}]".format(text))
  elif result.reason == speechsdk.ResultReason.Canceled:
      cancellation_details = result.cancellation_details
      print("Speech synthesis canceled: {}".format(cancellation_details.reason))
      if cancellation_details.reason == speechsdk.CancellationReason.Error:
          print("Error details: {}".format(cancellation_details.error_details))

