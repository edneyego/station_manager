from typing import Iterable, Optional, Protocol

from domain.models.station_model import StationModel


class StationRepositoryPort(Protocol):
    """
    Contrato do repositório de Estação.
    Implementações devem:
    - Executar 'save' e 'save_many' como upsert por codigo_estacao.
    - Levantar exceções de infraestrutura em falhas (ex.: RepositoryError).
    """

    def save(self, station: StationModel) -> bool:
        """Upsert por codigo_estacao. Retorna True se persistiu com sucesso."""
        ...

    def save_many(self, stations: Iterable[StationModel]) -> int:
        """Upsert em lote. Retorna total afetado (matched + upserted)."""
        ...

    def list_all_stations(self) -> Iterable[StationModel]:
        """Lista todas as estações (pode ser gerador/stream para evitar alta memória)."""
        ...

    def find_by_code(self, code: str) -> Optional[StationModel]:
        """Busca por codigo_estacao. Retorna None se não encontrar."""
        ...

    def remove_by_code(self, code: str) -> int:
        """Remove por codigo_estacao. Retorna quantos registros foram removidos (0/1)."""
        ...
