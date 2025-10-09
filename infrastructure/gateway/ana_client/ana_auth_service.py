import time
import requests

from infrastructure.settings.settings import get_settings


class AnaAuthService:
    def __init__(self):
        self.settings = get_settings()
        self.token_expiration: float = 0
        self.cached_headers: dict | None = None

    def _fetch_token(self) -> dict:
        response = requests.get(
            self.settings.ana_api_url,
            headers={
                "identificador": self.settings.ana_identificador,
                "senha": self.settings.ana_senha
            },
            timeout=self.settings.request_timeout
        )
        response.raise_for_status()
        token = response.json()["items"]["tokenautenticacao"]
        return {
            "Authorization": f"Bearer {token}",
            "accept": "*/*"
        }

    def get_auth_headers(self) -> dict:
        if not self.cached_headers or time.time() >= self.token_expiration:
            self.cached_headers = self._fetch_token()
            self.token_expiration = time.time() + 580  # duração do token com margem de segurança
        return self.cached_headers
