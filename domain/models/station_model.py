from datetime import datetime

from pydantic import BaseModel


class StationModel(BaseModel):
    ponto: str
    codigo_estacao: str
    id_noaa: str
    conversor: int
    sensor: str
    bacia: str
    nome_estacao: str | None = None
    nome_bacia: str | None = None
    rio_nome: str | None = None
    altitude: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    data_periodo_escala_inicio: datetime | None = None
    dado_manual: bool = False
    data_forecast: bool = False
    cota_min: int | None = None
    janela: int | None = None
    previsao: int | None = None
