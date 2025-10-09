from abc import ABC, abstractmethod
from typing import Any



class AnaClientPort(ABC):
    @abstractmethod
    def fetch_data(self, codigo: str) -> Any:
        pass