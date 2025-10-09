import requests
from typing import Any

from domain.ports.ana_client_port import AnaClientPort
from infrastructure.gateway.ana_client.ana_auth_service import AnaAuthService
from infrastructure.settings.settings import get_settings


class AnaApiClient(AnaClientPort):
    def __init__(self):
        self.auth_service = AnaAuthService()
        self.settings = get_settings()

    def fetch_data(self, codigo: str) -> Any:
        headers = self.auth_service.get_auth_headers()
        headers["accept"] = "*/*"  # igual ao curl

        # 🔑 Usa os nomes dos parâmetros exatamente como no cURL
        params = {
            "Código da Estação": codigo,
        }

        response = requests.get(
            self.settings.ana_api_inventario_url,
            headers=headers,
            params=params,  # requests faz a URL-encoding automaticamente
            timeout=self.settings.request_timeout
        )
        response.raise_for_status()
        return response.json()
