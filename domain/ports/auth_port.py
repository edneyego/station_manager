from abc import ABC, abstractmethod
from datetime import timedelta

class AuthTokenProvider(ABC):
    @abstractmethod
    def create_access_token(self, data: dict, expires_delta: timedelta) -> str:
        pass

    @abstractmethod
    def verify_token(self, token: str) -> dict:
        pass
