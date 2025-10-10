import os
from dotenv import load_dotenv
from datetime import timedelta

from application.controller.dependencies.token_response import TokenResponse
from domain.ports.auth_port import AuthTokenProvider
from domain.service.authenticator import Authenticator
from infrastructure.exceptions.auth_error import AuthError
from infrastructure.settings.settings import get_settings

class JWTAuthenticator(Authenticator):
    def __init__(self, token_provider: AuthTokenProvider):
        self.token_provider = token_provider
        self.s = get_settings()
        self.EXPECTED_USERNAME = self.s.user_name
        self.EXPECTED_PASSWORD = self.s.user_password

    def authenticate(self, username: str, password: str) -> TokenResponse:
        if username != self.EXPECTED_USERNAME or password != self.EXPECTED_PASSWORD:
            raise AuthError("Usuário ou senha inválidos", 401)

        token = self.token_provider.create_access_token(
            data={"sub": username},
            expires_delta=timedelta(hours=8)
        )
        return TokenResponse(access_token=token)
