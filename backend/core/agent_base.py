from abc import ABC, abstractmethod
from typing import Dict, Any

class Agent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(
        self,
        input_data: Dict[str, Any],
        tutor_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass
