from workers.exa import ExaSearch
from workers.claude import Claude
from workers.storage import SaveFiles
from workers.gemini import Gemini
from Poubelle.simulated_integration import SimulationStrategy, SimulationPlan


class WorkerRegistry:
    def __init__(
        self,
        search_worker: ExaSearch,
        claude_worker: Claude,
        storage: SaveFiles,
        simulation_strategy: SimulationStrategy,
        simulation_plan: SimulationPlan,
        # simulation_content_prospector: SimulationContentProspector,
        gemini_worker: Gemini
    ):
        self.search_worker = search_worker
        self.claude_worker = claude_worker
        self.storage = storage
        self.simulation_strategy = simulation_strategy
        self.simulation_plan = simulation_plan
        self.gemini_worker = gemini_worker
        # simulation_content_prospector: SimulationContentProspector()
