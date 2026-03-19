from pathlib import Path
from loguru import logger
from models.context import UserContext
import yaml
import json
import re
from models.schemas import Category



def clean_research_results(text: str) -> str:
    if not text:
        return ""
    # Dégage les pointillés et numéros de pages (Sommaires PDF)
    text = re.sub(r'\.{2,}\s*[pP]?\.\?\s*\d*', '', text)
    # Nettoyage final : symboles chelous et normalisation des espaces
    text = re.sub(r'[#\[\]\{\}\*]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class SaveFiles:
    def __init__(self):
        # main_path = Path(f"content/{name}/intermediate_steps")
        # self.plan_path = f"{main_path}/plan.json"
        # self.strategy_path = f"{main_path}/strategy.json"
        # self.
        pass

    def _sanitize_filename(self, name):
        clean_name = name.lower().replace(" ", "_")
        clean_name = re.sub(r'[^\w\-_.]', '', clean_name)
        sanitize_name = "".join([c if c.isalnum() or c in "_-" else "_" for c in clean_name])
        return sanitize_name

    def _define_path(self, user_context: UserContext, phase="", research_topic=""):
        name = self._sanitize_filename(user_context.name)
        parts = ["content", name, "intermediate_steps"]

        if phase:
            parts.append(phase)
            if research_topic:
                parts.append(self._sanitize_filename(research_topic))
        
        return Path(*parts)


    def define_file_name(self, category: Category, user_context: UserContext, phase="", research_topic="", title="", id = None):
        path = self._define_path(user_context, phase, research_topic)

        match category:
            case Category.PLAN:
                file_name = f"{path}/plan.json"
            case Category.STRATEGY:
                file_name = f"{path}/strategy.dsv"
            case Category.REDACTION:
                file_name = f"{path}/redaction_{id}.txt"
            case Category.RESEARCH:
                title = self._sanitize_filename(title)
                file_name = f"{path}/{title}.json"
            case Category.PROSPECTOR:
                file_name = f"{path}/content_prospector.dsv"
            case Category.RESEARCH_CONCATENATED:
                file_name = f"{path}/research_concatenated_{phase}.dsv"
            case Category.VERIFIED_RESEARCH:
                file_name = f"{path}/verified_research.dsv"
            case Category.VERIFIED_RESEARCH_CONCATENATED:
                file_name = f"{path}/verified_research_concatenated_{phase}.dsv"
            case Category.PHONEMES:
                file_name = f"{path}/phonemes.json"
            case Category.AUDIO:
                file_name = f"{path}/audio_{id}.mp3"
            case Category.REDACTION_WITH_SSML:
                file_name = f"{path}/redaction_with_ssml_{id}.txt"
            case Category.REDACTION_HISTORY:
                file_name = f"{path}/redaction_history_{id}.json"
            case _:
                logger.error(f"Category {category} not found!")
                raise ValueError(f"Category {category} not found!")

        return file_name

    def save(self, category: Category, user_context: UserContext, content, id = None):
        if not content:
            logger.error(f"Content is empty for category {category}!")
            raise ValueError(f"Content is empty for category {category}!")

        file_name = self.define_file_name(category, user_context, id=id)
        path = Path(file_name).parent
        path.mkdir(parents=True, exist_ok=True)

        extension = Path(file_name).suffix
        match extension:
            case ".json":
                if hasattr(content, "model_dump_json"): # For pydantic objects
                    with open(file_name, "w", encoding="utf-8") as f:
                        f.write(content.model_dump_json(indent=4))
                else:
                    with open(file_name, "w", encoding="utf-8") as f:
                        json.dump(content, f, indent=4, ensure_ascii=False)                    
            case ".mp3":
                with open(file_name, "wb") as f:
                    f.write(content)
            case _:
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(content)

    def loads(self, category: Category, user_context: UserContext, id = None, pydantic_model = None):
        file_name = self.define_file_name(category, user_context, id = id)
        logger.debug(f"file_name : {file_name}")


        
        if not Path(file_name).exists():
            logger.warning(f"{category} File missing!")

        with open(file_name, "r", encoding="utf-8") as f:
            extension = Path(file_name).suffix
            match extension:
                case ".json":
                    file = json.load(f)
                    if pydantic_model:
                        return pydantic_model.model_validate(file)
                    else:
                        return file
                case _:
                    return f.read()

    def does_exist(self, category: Category, user_context: UserContext, id = None):
        file_name = self.define_file_name(category, user_context, id = id)
        return Path(file_name).exists()

    def save_research(self, category: Category, user_context: UserContext, content, phase, research_topic="", title = ""):
        if not content:
            logger.error(f"Content is empty for category {category}!")
            raise ValueError(f"Content is empty for category {category}!")

        file_name = self.define_file_name(category, user_context, phase, research_topic, title)
        path = Path(file_name).parent
        path.mkdir(parents=True, exist_ok=True)
        
        extension = Path(file_name).suffix
        with open(file_name, "w", encoding="utf-8") as f:
            match extension:
                case ".json":
                    if hasattr(content, "model_dump_json"): # For pydantic objects
                        f.write(content.model_dump_json(indent=4))
                    else:
                        json.dump(content, f, indent=4, ensure_ascii=False)                    
                case _:
                        f.write(content)
            

    def loads_research(self, category: Category, user_context: UserContext, phase, research_topic, title=""):
        file_name = self.define_file_name(category, user_context, phase, research_topic, title)

        if Path(file_name).exists():
            extension = Path(file_name).suffix

            match extension:
                case ".json":
                    with open(file_name, "r", encoding="utf-8") as f:
                        file = json.load(f)
                        if type(file) == str:
                            # Sometime the LLM return json with a double encoding...
                            file = json.loads(file) 
                        return file
                case _:
                    with open(file_name, "r", encoding="utf-8") as f:
                        return f.read()
        else:
            logger.warning("Research file missing!")

    def does_exist_research(self, category: Category, user_context: UserContext, phase, research_topic, title=""):
        args = [category, user_context, phase, research_topic]
        if title:
            args.append(title)
        
        file_name = self.define_file_name(*args)
        return Path(file_name).exists()

    def loads_all_research(self, category: Category, user_context: UserContext, phase, research_topic):
        """Loads all the json of a given """
        path = self._define_path(user_context, phase, research_topic)

        research_list = []

        for file in path.rglob("*"):
            extension = Path(file).suffix
            if extension == ".json":
                with open(file, "r", encoding="utf-8") as f:
                    loaded_file = json.load(f)
                    research_list.append(loaded_file)
        return research_list

    def loads_all_verifed_research(self, user_context: UserContext, phase):
        path = self._define_path(user_context, phase)
        list = []

        for file in path.rglob("*"):
            name = file.name
            if name == f"verified_research.dsv":
                with open(file, "r", encoding="utf-8") as f:
                    list.append(f.read())   
        return list

                