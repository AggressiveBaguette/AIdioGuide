from models.context import UserContext
import asyncio
import asyncio
import os
from services.orchestrator import orchestrator
from config import Languages
from loguru import logger

logger.remove() 


def custom_filter(record):
    if record["level"].no >= logger.level("INFO").no:
        return True
    
    if record["level"].name == "DEBUG":
    #     # Filtering by file
        if record["name"] == "__main__":
            return True
        if "claude.py" in record["file"].name:
            return True
        # if "researcher.py" in record["file"].name:
        #     return True
    #     if "exa.py" in record["file"].name:
    #         return True
        if "gemini.py" in record["file"].name:
            return True
        if "azureTTS.py" in record["file"].name:
            return True
        if "phonemes_detection.py" in record["file"].name:
            return True
        if "audio_generation.py" in record["file"].name:
            return True
        if "content_verifier.py" in record["file"].name:
            return True
        

        # Filtering by function
        if record["function"] in ["_perform_and_save_web_search", "_perform_web_searches", "_get_relevant_facts"]:
            return True
        
            
    return False

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
        city="Sceaux",
        language=Languages.fr_FR,
        name = "Sceaux-001",        
        comment = "Audioguide très court, 4-5 arrêts max. 10' d'audio max."


    )
    await orchestrator(user_context)

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
