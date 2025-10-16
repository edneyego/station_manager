import datetime
import logging
from typing import Iterable, Any

from pydantic import field_validator

from domain.models.station_model import StationModel
from domain.ports.ana_client_port import AnaClientPort
from infrastructure.gateway.ana_client.ana_api_client import AnaApiClient


class StationInformation:
    _FIELDS_TO_FILL: tuple[str, ...] = (
        "nome_estacao",
        "nome_bacia",
        "rio_nome",
        "altitude",
        "latitude",
        "longitude",
        "data_periodo_escala_inicio",
    )

    def __init__(self):
        self.ana_client: AnaClientPort = AnaApiClient()

    def get_additional_information(self, station: StationModel):
        if not self._needs_enrichment(station, self._FIELDS_TO_FILL):
            return station

        resp = self.ana_client.fetch_data(codigo=station.codigo_estacao) or {}
        station_info = resp.get("items") or []
        if not station_info:
            logging.warning(f"Não foram encontrado dados adicionais para a estação {station.codigo_estacao}")
            logging.warning(station_info)
            return station

        for itens in station_info:
            station.nome_estacao = itens.get("Estacao_Nome")
            station.nome_bacia = itens.get("Bacia_Nome")
            station.rio_nome = itens.get("Rio_Nome")
            station.altitude = itens.get("Altitude")
            station.latitude = itens.get("Latitude")
            station.longitude = itens.get("Longitude")
            raw = itens.get("Data_Periodo_Escala_Inicio") or "1900-01-01 00:00:00"
            station.data_periodo_escala_inicio = raw if isinstance(raw, datetime.datetime) else datetime.datetime.fromisoformat(
                raw.replace(' ', 'T'))

        return station

    @staticmethod
    def _needs_enrichment(obj: Any, fields: Iterable[str]) -> bool:
        """True se ALGUM campo estiver None ou string vazia."""
        for f in fields:
            v = getattr(obj, f, None)
            if v is None:
                return True
            if isinstance(v, str) and v.strip() == "":
                return True
        return False
