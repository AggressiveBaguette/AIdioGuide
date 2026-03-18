

class PlanService:
    def __init__(self, user_context: UserContext, registery : WorkerRegistry):
        self.user_context = user_context
        self.registery = registery