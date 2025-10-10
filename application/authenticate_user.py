from application.controller.dependencies.token_response import TokenResponse
from domain.service.authenticator import Authenticator


class AuthenticateUser:
    def __init__(self, authenticator: Authenticator):
        self.authenticator = authenticator

    def __call__(self, username: str, password: str) -> TokenResponse:
        return self.authenticator.authenticate(username, password)