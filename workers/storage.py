from pathlib import Path
from loguru import logger
from models.context import UserContext
import yaml
import json
import re
from models.schemas import Category




class SaveFiles:
    def __init__(self):
        pass

    def _sanitize_filename(self, name):
        clean_name = name.lower().replace(" ", "_")
        clean_name = re.sub(r'[^\w\-_.]', '', clean_name)
        sanitize_name = "".join([c if c.isalnum() or c in "_-" else "_" for c in clean_name])
        return sanitize_name

    def _define_path(self, category: Category, user_context: UserContext, phase="", research_topic=""):
        name = self._sanitize_filename(user_context.name)
        # Define main path to the audioguide
        parts = ["content", name, "final_results"]

        if phase:
            parts.append(phase)
            if research_topic:
                parts.append(self._sanitize_filename(research_topic))
        
        return Path(*parts)


    def define_file_name(self, category: Category, user_context: UserContext, phase="", research_topic="", title="", id = None):
        path = self._define_path(user_context, phase, research_topic)

        if research_topic:
            research_path = self._sanitize_filename(research_topic)
        match category:
            case Category.STRATEGY:
                file_name = f"{path}/01_strategy.dsv"
            case Category.PROSPECTOR:
                file_name = f"{path}/02_Research/{phase}/{research_path}/02.1_unverified_research.dsv"
            case Category.RESEARCH:
                title = self._sanitize_filename(title)
                file_name = f"{path}/02_Research/{phase}/{research_path}/facts/{title}.json"
            case Category.RESEARCH_CONCATENATED:
                file_name = f"{path}/02_Research/{phase}/{research_path}/02.2_concatenated_facts_{phase}.dsv"
            case Category.VERIFIED_RESEARCH:
                file_name = f"{path}/02_Research/{phase}/{research_path}/02.3_verified_research.dsv"
            case Category.VERIFIED_RESEARCH_CONCATENATED:
                file_name = f"{path}/02_Research/02.4_concatenated_verified_facts_{phase}.dsv"
            case Category.PLAN:
                file_name = f"{path}/03_plan.json"
            case Category.REDACTION:
                file_name = f"{path}/04_Scripts/{id}.txt"
            case Category.REDACTION_HISTORY:
                file_name = f"{path}/04_Scripts/Conversation_history/{id}.json"
            case Category.PHONEMES:
                file_name = f"{path}/05_phonemes.json"
            case Category.REDACTION_WITH_SSML:
                file_name = f"{path}/06_Scripts_with_SSML/{id}.txt"
            case Category.AUDIO:
                file_name = f"{path}/07_Audio/{id}.mp3"
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

    # def loads_all_research(self, category: Category, user_context: UserContext, phase, research_topic):
    #     """Loads all the json of a given """
    #     path = self._define_path(user_context, phase, research_topic)

    #     research_list = []

    #     for file in path.rglob("*"):
    #         extension = Path(file).suffix
    #         if extension == ".json":
    #             with open(file, "r", encoding="utf-8") as f:
    #                 loaded_file = json.load(f)
    #                 research_list.append(loaded_file)
    #     return research_list

    # def loads_all_verifed_research(self, user_context: UserContext, phase):
    #     path = self._define_path(user_context, phase)
    #     list = []

    #     for file in path.rglob("*"):
    #         name = file.name
    #         if name == f"verified_research.dsv":
    #             with open(file, "r", encoding="utf-8") as f:
    #                 list.append(f.read())   
    #     return list

                