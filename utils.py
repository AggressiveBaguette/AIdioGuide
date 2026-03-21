from loguru import logger
import time
import re
from pathlib import Path

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

def parse_LLM_output(llm_response, pydantic_schema):
    # Delete markdown json LLM often sends at the beginning of its response...
    match = re.search(r"```json\s*(.*?)\s*```", llm_response, re.DOTALL)

    # First group is the json markdown, so we select the second
    json_str = match.group(1).strip() if match else llm_response.strip()

    try:
        validated_data = pydantic_schema.model_validate_json(json_str)
        return validated_data

    except Exception as e:
        logger.error(f"LLM response : {llm_response}")
        logger.error(f"[Error]: {e}")
        raise e
        
def is_rate_limit_error(exception):
    return getattr(exception, "status_code", None) == 429