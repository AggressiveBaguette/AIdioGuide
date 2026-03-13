from models.context import UserContext
import asyncio
from dotenv import load_dotenv
load_dotenv('.env')

import asyncio
import os
import pyaudio
import time
import re
from cartesia import Cartesia
from utils import timer_debug, save_LLM_output
from Poubelle.tts_integration import CartesiaWorker
from services.orchestrator import orchestrator
from workers.exa import ExaSearch
import json
from workers.claude import Claude

from google import genai
from google.genai import types
from loguru import logger
import sys

client = genai.Client()
# cartesia_client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))
cartesia_api_key = os.getenv("CARTESIA_API_KEY")

logger.remove() 

# 2. Une seule ligne, pas de filtre, canal stdout (comme print)
# logger.add(sys.stdout, level="DEBUG", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {name}:{function}:{line} - {message}")
# 3. Test immédiat

def custom_filter(record):
    # 1. On laisse TOUT passer à partir de INFO (Warning, Error, etc.)
    if record["level"].no >= logger.level("INFO").no:
        return True
    
    # 2. Pour le DEBUG, on définit nos cibles
    if record["level"].name == "DEBUG":
    #     # Toujours voir les DEBUG de main
    #     if record["name"] == "__main__":
    #         return True
    #     # On accepte si c'est le fichier qu'on investigue
        if "claude.py" in record["file"].name:
            return True
    #     if "researcher.py" in record["file"].name:
    #         return True
    #     if "exa.py" in record["file"].name:
    #         return True
    #     if "gemini.py" in record["file"].name:
    #         return True

    #     # On peut aussi filtrer par fonction précise
        if record["function"] in ["plan"]:
            return True
        
            
    return False

logger.add(sys.stdout, filter=custom_filter, level="DEBUG")


# --- pyaudio config ---
FORMAT = pyaudio.paFloat32
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 44100
CHUNK_SIZE = 1024

pya = pyaudio.PyAudio()

# --- Live API config ---
conversation_history = []

# @timer_debug 
# async def get_text_response():
#     # Appel LLM pour générer texte
#     try:
#         response = client.models.generate_content(
#             model=TEXT_MODEL, contents='Why is the sky blue? 20 words max.'
#         )
#         # print(response)
#         # print("--------")
#         # print(response.candidates[0].content.parts[0].text)
#         return response.candidates[0].content.parts[0].text
#     except Exception as e:
#         return f"[Error]: {e}"


async def audio_generation(audio_queue):

    stream = pya.open(
        format=FORMAT,            
        channels=CHANNELS,        
        rate=RECEIVE_SAMPLE_RATE, 
        output=True               
        )            

    while True: 
        content = await audio_queue.get() 
        
        if content is None:
            break
        
        stream.write(content)

    stream.stop_stream()
    stream.close()
    pya.terminate()      
        
async def test_cartesia():
    audio_queue = asyncio.Queue()
    worker = CartesiaWorker(api_key=cartesia_api_key, audio_restitution_mode="stream", audio_queue = audio_queue)
    worker_task = asyncio.create_task(worker.get_vocal_response())

    asyncio.create_task(audio_generation(audio_queue))

    await worker.push("Premier tour de chauffe.")
    await asyncio.sleep(5)


    await worker.push("Je push un truc à posteriori !")

    # Worker close 
    await worker.stop()
    await worker_task

    # Waiting for the audio queue to be fully consumme, otherwise, the audio will be cut
    await audio_queue.join()

async def generate_audio_guide():
    user_context = UserContext(
        # city="Paris, Quartier Latin",
        # language="Français",
        # name = "Paris-002",
        # comment = "Bonne connaissance historique, habite sur Paris, mais connait mieux la rive droite et le centre que la rive gauche. Focus sur les aspects historiques."
        city="Paris",
        language="Français",
        name = "Paris-003",        
        comment = "Je connais déjà très bien Paris et j'ai d'excellente connaissance en histoire. Je veux uniquement focus le Paris médiéval."
        # city="Beyrouth, Liban",
        # language="Français",
        # name = "Beyrouth-001",        
        # comment = "Passionné d'histoire, avec une bonne connaissance de l'histoire high-level Européen mais n'a jamais été au Liban ou au Moyen-Orient. Veut visiter la ville."

    )
    await orchestrator(user_context)

async def generate_exa(query):
    exa_worker = ExaSearch()
    exa_worker.search(query)
    
    filename = f"exa_results/{sanitize_filename(query)}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(exa_worker.search(query), f, indent=4, ensure_ascii=False)

async def test():
    content = """ """
 
    worker = Claude(content)
    response = worker.get_text()
    print(response)
    save_LLM_output(response, "claude_mythomane_erudit")

if __name__ == "__main__":
    try:
        # 1. On vire tout le bordel précédent

        # asyncio.run(main())
        asyncio.run(generate_audio_guide())
        # asyncio.run(generate_exa("Cour des Miracles faubourg Saint-Marcel rue Mouffetard emplacement exact XVIIe siècle sources historiques"))
        # asyncio.run(generate_exa("La Reynie rafle Cour des Miracles 1667 Louis XIV résultats dispersion populations"))
        # asyncio.run(generate_exa("Victor Hugo Notre-Dame de Paris Cour des Miracles sources historiques inspiration faubourg Saint-Marcel"))

        # asyncio.run(test())

    except KeyboardInterrupt:
        print("Interrupted by user.")
