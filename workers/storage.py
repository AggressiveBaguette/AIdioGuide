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

    def _define_path(self, user_context: UserContext, phase="", research_topic=""):
        name = self._sanitize_filename(user_context.name)
        # Define main path to the audioguide
        parts = ["content", name]
                
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
                file_name = f"{path}/02_Research/{phase}/{research_path}/02.2_concatenated_facts.dsv"
            case Category.VERIFIED_RESEARCH:
                file_name = f"{path}/02_Research/{phase}/{research_path}/02.3_verified_research.dsv"
            case Category.VERIFIED_RESEARCH_CONCATENATED:
                file_name = f"{path}/02_Research/{phase}/02.4_concatenated_verified_facts_{phase}.dsv"
            case Category.PLAN:
                file_name = f"{path}/03_plan.json"
            case Category.REDACTION:
                file_name = f"{path}/04_Scripts/{int(id):02d}.txt"
            case Category.REDACTION_HISTORY:
                file_name = f"{path}/04_Scripts/Conversation_history/{int(id):02d}.json"
            case Category.PHONEMES:
                file_name = f"{path}/05_phonemes.json"
            case Category.REDACTION_WITH_SSML:
                file_name = f"{path}/06_Scripts_with_SSML/{int(id):02d}.txt"
            case Category.AUDIO:
                file_name = f"{path}/07_Audio/{int(id):02d}.mp3"
            case _:
                logger.error(f"Category {category} not found!")
                raise ValueError(f"Category {category} not found!")

        return file_name

    def save(self, category: Category, user_context: UserContext, content, phase="", research_topic="", title="", id=None):
        if not content:
            logger.error(f"Content is empty for category {category}!")
            raise ValueError(f"Content is empty for category {category}!")

        file_name = self.define_file_name(category, user_context, phase=phase, research_topic=research_topic, title=title, id=id)
        path = Path(file_name).parent
        path.mkdir(parents=True, exist_ok=True)

        extension = Path(file_name).suffix
        match extension:
            case ".json":
                if hasattr(content, "model_dump_json"):  # For pydantic objects
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

    def loads(self, category: Category, user_context: UserContext, phase="", research_topic="", title="", id=None, pydantic_model=None):
        file_name = self.define_file_name(category, user_context, phase=phase, research_topic=research_topic, title=title, id=id)
        logger.debug(f"file_name : {file_name}")

        if not Path(file_name).exists():
            logger.error(f"{category} File missing: {file_name}")
            raise FileNotFoundError(f"{category} File missing: {file_name}")

        with open(file_name, "r", encoding="utf-8") as f:
            extension = Path(file_name).suffix
            match extension:
                case ".json":
                    file = json.load(f)
                    if type(file) == str:
                        # Sometime the LLM returns json with a double encoding...
                        file = json.loads(file)
                    if pydantic_model:
                        return pydantic_model.model_validate(file)
                    return file
                case _:
                    return f.read()

    def does_exist(self, category: Category, user_context: UserContext, phase="", research_topic="", title="", id=None):
        file_name = self.define_file_name(category, user_context, phase=phase, research_topic=research_topic, title=title, id=id)
        return Path(file_name).exists()
