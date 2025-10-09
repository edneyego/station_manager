from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repo: MongoStationRepository = Depends(get_station_repo),
):
    try:
        items = repo.list_all_stations()
        # Se seu repo passar a aceitar paginação no find(), troque por skip/limit no Mongo
        return items[skip: skip + limit]
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
):
    try:
        deleted = repo.remove_station_by_code_station(code_station=codigo_estacao)
        if deleted == 0:
            raise HTTPException(status_code=404, detail="Estação não encontrada")
        return {"status": "ok", "deleted": deleted}
    except RepositoryError as e:
        raise HTTPException(status_code=500, detail=str(e))
