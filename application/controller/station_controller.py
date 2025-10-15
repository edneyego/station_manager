from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from application.controller.dependencies.authenticate_user_dependence import get_current_user
from domain.models.station_model import StationModel
from infrastructure.repository.station_repository import (
    MongoStationRepository,
    RepositoryError,
)

router = APIRouter(prefix="/stations", tags=["Estações"])

# ----- Dependency Injection (poderia ser singleton/pool se preferir) -----
def get_station_repo() -> MongoStationRepository:
    return MongoStationRepository()

# -----------------------
# CRUD endpoints
# -----------------------

@router.post(
    "",
    response_model=StationModel,
    status_code=status.HTTP_201_CREATED,
    summary="Cria/atualiza (upsert) uma estação",
)
def create_station(
    station: StationModel,
    repo: MongoStationRepository = Depends(get_station_repo),
    user=Depends(get_current_user)
):
    try:
        repo.save(station=station)  # upsert
        return station
    except RepositoryError as e:
        # erro da camada infra
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/estacoes_lote",
    status_code=status.HTTP_200_OK,
    summary="Cria/atualiza (upsert) múltiplas estações",
)
def create_many_stations(
    stations: List[StationModel],
    repo: MongoStationRepository = Depends(get_station_repo),
    user=Depends(get_current_user)
):
    try:
        affected = repo.save_many(stations=stations)
        return {"status": "ok", "affected": affected}
    except RepositoryError as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "",
    response_model=List[StationModel],
    status_code=status.HTTP_200_OK,
    summary="Lista estações",
)
def list_stations(
    repo: MongoStationRepository = Depends(get_station_repo),
    dados_estacao_manual: Optional[bool] = Query(
        None,
        description="Filtra por estações manuais (true), não manuais (false). Omitir para retornar todas.",
    ),
):
    try:
        items = repo.list_all_stations(dados_estacao_manual=dados_estacao_manual)
        # Se seu repo passar a aceitar paginação no find(), troque por skip/limit no Mongo
        return items
    except RepositoryError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{codigo_estacao}",
    response_model=StationModel,
    status_code=status.HTTP_200_OK,
    summary="Obtém uma estação por código",
)
def get_station_by_code(
    codigo_estacao: str,
    repo: MongoStationRepository = Depends(get_station_repo),
):
    try:
        st = repo.find_station_by_code_station(code_station=codigo_estacao)
        if not st:
            raise HTTPException(status_code=404, detail="Estação não encontrada")
        return st
    except RepositoryError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{codigo_estacao}",
    status_code=status.HTTP_200_OK,
    summary="Remove uma estação por código",
)
def delete_station_by_code(
    codigo_estacao: str,
    repo: MongoStationRepository = Depends(get_station_repo),
    user=Depends(get_current_user)
):
    try:
        deleted = repo.remove_station_by_code_station(code_station=codigo_estacao)
        if deleted == 0:
            raise HTTPException(status_code=404, detail="Estação não encontrada")
        return {"status": "ok", "deleted": deleted}
    except RepositoryError as e:
        raise HTTPException(status_code=500, detail=str(e))
