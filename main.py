from models.context import UserContext
from dotenv import load_dotenv
import asyncio
import os
from services.orchestrator import orchestrator
from config import Languages
from loguru import logger
import sys

logger.remove() 

def custom_filter(record):
    # Define custom filters to only show logs 
    if record["level"].no >= logger.level("INFO").no:
        return True
    
    if "claude.py" in record["file"].name:
        return True
    if "gemini.py" in record["file"].name:
            return True        
            
    return False

logger.add(sys.stdout, filter=custom_filter, level="DEBUG")

def verify_secrets():
    load_dotenv()

    requiered_keys = [
        "GOOGLE_API_KEY",
        "EXA_API_KEY",
        "ANTHROPIC_API_KEY",
        "AZURE_API_KEY",
        "AZURE_REGION"
    ]

    missing_keys = [key for key in requiered_keys if not os.getenv(key)]

    if missing_keys:
        logger.error(f"Missing keys: {missing_keys}")
        raise ValueError(f"Missing keys: {missing_keys}")

async def generate_audio_guide():
    user_context = UserContext(
        # city="Paris, Quartier Latin",
        # language="Français",
        # name = "Paris-002",
        # comment = "Bonne connaissance historique, habite sur Paris, mais connait mieux la rive droite et le centre que la rive gauche. Focus sur les aspects historiques."
        # city="Paris",
        # language=Languages.fr_FR,
        # name = "Paris-003",        
        # comment = "Je connais déjà très bien Paris et j'ai d'excellente connaissance en histoire. Je veux uniquement focus le Paris médiéval."
        # city="Beyrouth, Liban",
        # language="Français",
        # name = "Beyrouth-001",        
        # comment = "Passionné d'histoire, avec une bonne connaissance de l'histoire high-level Européen mais n'a jamais été au Liban ou au Moyen-Orient. Veut visiter la ville."
        # city="Fontenay-aux-Roses",
        # language=Languages.fr_FR,
        # name = "FaR-001",        
        # comment = "Audioguide très court, 5-6 arrêts max. 15' d'audio max."
        # city="Sceaux",
        # language=Languages.fr_FR,
        # name = "Sceaux-001",        
        # comment = "Audioguide très court, 4-5 arrêts max. 10' d'audio max."
        city="Paris",
        language=Languages.fr_FR,
        name = "Paris-004",        
        comment = "J'ai d'excellente connaissance en histoire et je connais parfaitement Paris. Je veux un tour uniquement focus sur le Paris médiéval."


    )
    await orchestrator(user_context)

if __name__ == "__main__":
    try:
        verify_secrets()
        asyncio.run(generate_audio_guide())

    except KeyboardInterrupt:
        print("Interrupted by user.")
