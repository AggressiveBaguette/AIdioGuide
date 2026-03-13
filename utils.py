from asyncio.log import logger
import time
import functools
import re
from pathlib import Path


def timer_debug(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs): # On le rend async
        start = time.perf_counter()
        
        # On attend l'exécution réelle ici
        result = await func(*args, **kwargs) 
        
        end = time.perf_counter()
        print(f"[{func.__name__}] Exécuté en {end - start:.4f}s")
        return result
    return wrapper

def extract_first_sentence(buffer):
    new_buffer = buffer
    sentence_extracted = ""
    first_sentence_regex = r"(.*?[.!?])"


    first_sentence = re.search(first_sentence_regex, buffer)

    if first_sentence:
        sentence_extracted = first_sentence.group().strip()
        new_buffer = buffer[first_sentence.end():].strip()
    # print(f"extract {new_buffer}")

    # print(f"extract phrase  {sentence_extracted}")
    return new_buffer, sentence_extracted

def save_LLM_output(content, model_name):
    path = Path(f"logs")
    path.mkdir(parents=True, exist_ok=True)

    timestamp = time.time()

    with open(path / f"{model_name}_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write(str(content))
    logger.debug(f"LLM Output saved")
