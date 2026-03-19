from models.schemas import ResearchTopic
from loguru import logger
from string import Template
from typing import TYPE_CHECKING
from models.schemas import Strategy, ResearchTopic

if TYPE_CHECKING:
    from models.context import UserContext
    from models.registry import WorkerRegistry

class PlanService:
    def __init__(self, user_context: UserContext, registery : WorkerRegistry):
        self.user_context = user_context
        self.registery = registery