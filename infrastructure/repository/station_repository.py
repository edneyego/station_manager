import logging
from typing import Iterable, List, Optional

from pymongo import MongoClient, ReplaceOne, errors as mg_errors
from pymongo.synchronous.collection import Collection

from domain.models.station_model import StationModel
from domain.ports.station_repository_port import StationRepositoryPort
from domain.service.stations_info import StationInformation
from infrastructure.exceptions.repository_error import RepositoryError
from infrastructure.settings.settings import get_settings

log = logging.getLogger(__name__)

class MongoStationRepository(StationRepositoryPort):
    """
    Implementação MongoDB do StationRepositoryPort, com tratamento de erros.
    - Enriquecimento de estação via StationInformation (falha não bloqueia persistência).
    - Criação de índice (unique) em 'codigo_estacao'.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        try:
            self.client = MongoClient(
                self.settings.mongo_uri,
                serverSelectionTimeoutMS=5000,  # evita pendurar fio em ambientes ruins
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
            )
            # Força um ping inicial para falhas rápidas de conexão
            self.client.admin.command("ping")
        except mg_errors.PyMongoError as e:
            log.exception("Falha ao conectar ao MongoDB.")
            raise RepositoryError(f"Falha ao conectar ao MongoDB: {e}") from e

        try:
            self.db = self.client[self.settings.mongo_db_name]
            self.collection: Collection = self.db["estacoes"]
            # Garante índice único por codigo_estacao
            self.collection.create_index("codigo_estacao", unique=True, name="uk_codigo_estacao")
        except mg_errors.PyMongoError as e:
            log.exception("Falha ao preparar a coleção/índices.")
            raise RepositoryError(f"Falha ao preparar a coleção/índices: {e}") from e

        # Serviço de enriquecimento (não levanta exceção para não acoplar repositório a rede)
        self.station_information = StationInformation()

    # ---------------------------
    # Operações de escrita
    # ---------------------------

    def save(self, station: StationModel) -> bool:
        """
        Upsert por codigo_estacao.
        Retorna True se houve upsert com sucesso.
        Lança RepositoryError para erros de Mongo.
        """
        try:
            # Tenta enriquecer, mas não bloqueia persistência se falhar
            try:
                station = self.station_information.get_additional_information(station=station)
            except Exception:
                log.warning("Falha no enriquecimento da estação %s. Seguindo com persistência.",
                            getattr(station, "codigo_estacao", "?"), exc_info=True)

            payload = station.model_dump(exclude_none=True)
            res = self.collection.replace_one(
                {"codigo_estacao": station.codigo_estacao},
                payload,
                upsert=True,
            )
            # acknowledged sempre True com drivers modernos; consideramos sucesso se não lançou exceção
            return True
        except mg_errors.DuplicateKeyError as e:
            # Em teoria não acontece num replace_one com filtro por codigo_estacao, mas deixamos por segurança
            log.exception("Violação de chave única em save(%s).", station.codigo_estacao)
            raise RepositoryError(f"Duplicidade detectada para codigo_estacao={station.codigo_estacao}: {e}") from e
        except mg_errors.PyMongoError as e:
            log.exception("Erro Mongo ao salvar estação %s.", station.codigo_estacao)
            raise RepositoryError(f"Erro ao salvar estação {station.codigo_estacao}: {e}") from e

    def save_many(self, stations: Iterable[StationModel]) -> int:
        """
        Upsert em lote (bulk_write, ordered=False).
        Retorna o total de registros afetados (matched + upserted).
        Lança RepositoryError para erros graves de Mongo.
        """
        try:
            ops: List[ReplaceOne] = []

            for e in stations:
                # Enriquecimento best-effort
                try:
                    self.station_information.get_additional_information(station=e)
                except Exception:
                    log.warning("Falha no enriquecimento da estação %s durante bulk.",
                                getattr(e, "codigo_estacao", "?"), exc_info=True)

                ops.append(
                    ReplaceOne(
                        {"codigo_estacao": e.codigo_estacao},
                        e.model_dump(exclude_none=True),
                        upsert=True,
                    )
                )

            if not ops:
                return 0

            result = self.collection.bulk_write(ops, ordered=False)
            affected = (result.matched_count or 0) + (len(result.upserted_ids or {}) if result.upserted_ids else 0)
            return affected

        except mg_errors.BulkWriteError as e:
            # BulkWriteError tem detalhes parciais; tentamos extrair efeito parcial
            log.error("BulkWriteError em save_many: %s", e.details, exc_info=True)
            # Se quiser falhar de vez: raise RepositoryError(...)
            # Aqui tentamos retornar o que foi possível (parcial) se houver detalhes
            try:
                details = e.details or {}
                n_matched = int(details.get("nMatched", 0))
                n_upserted = int(details.get("nUpserted", 0))
                return n_matched + n_upserted
            except Exception:
                raise RepositoryError(f"Erro em operação bulk: {e}") from e

        except mg_errors.PyMongoError as e:
            log.exception("Erro Mongo em save_many.")
            raise RepositoryError(f"Erro ao salvar em lote: {e}") from e

    # ---------------------------
    # Operações de leitura
    # ---------------------------

    def list_all_stations(self) -> List[StationModel]:
        """
        Retorna todas as estações.
        Em falha, lança RepositoryError.
        """
        try:
            docs = list(self.collection.find({}))
            return [StationModel(**doc) for doc in docs]
        except mg_errors.PyMongoError as e:
            log.exception("Erro Mongo ao listar estações.")
            raise RepositoryError(f"Erro ao listar estações: {e}") from e
        except Exception as e:
            log.exception("Erro ao materializar StationModel na listagem.")
            raise RepositoryError(f"Erro ao montar modelos na listagem: {e}") from e

    def find_station_by_code_station(self, code_station: str) -> Optional[StationModel]:
        """
        Busca por codigo_estacao.
        Retorna StationModel ou None.
        Em falha, lança RepositoryError.
        """
        try:
            doc = self.collection.find_one({"codigo_estacao": code_station})
            return StationModel(**doc) if doc else None
        except mg_errors.PyMongoError as e:
            log.exception("Erro Mongo ao buscar estação %s.", code_station)
            raise RepositoryError(f"Erro ao buscar estação {code_station}: {e}") from e
        except Exception as e:
            log.exception("Erro ao materializar StationModel em find_station_by_code_station.")
            raise RepositoryError(f"Erro ao montar modelo da estação {code_station}: {e}") from e

    # ---------------------------
    # Operações de remoção
    # ---------------------------

    def remove_station_by_code_station(self, code_station: str) -> int:
        """
        Remove por codigo_estacao.
        Retorna a contagem de removidos (0 ou 1).
        Em falha, lança RepositoryError.
        """
        try:
            res = self.collection.delete_one({"codigo_estacao": code_station})
            return int(res.deleted_count or 0)
        except mg_errors.PyMongoError as e:
            log.exception("Erro Mongo ao remover estação %s.", code_station)
            raise RepositoryError(f"Erro ao remover estação {code_station}: {e}") from e