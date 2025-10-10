from abc import abstractmethod, ABC

from application.controller.dependencies.token_response import TokenResponse


class Authenticator(ABC):
    @abstractmethod
    def authenticate(self, username: str, password: str) -> TokenResponse:
        pass
