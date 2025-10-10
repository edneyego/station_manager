from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query

from application.controller.dependencies.authenticate_user_dependence import get_current_user
from domain.ports.station_repository_port import StationRepositoryPort
from infrastructure.repository.station_repository import MongoStationRepository

router = APIRouter(tags=["Estações em lote"])

def get_estacao_repository() -> StationRepositoryPort:
    # ponto único de troca do adapter (Mongo, SQL, mock, etc.)
    return MongoStationRepository()

@router.post("/station/import")
async def import_stations(
    upload: UploadFile = File(...),
    upsert_existing: bool = Query(False, description="Se true, atualiza registros existentes"),
    repo: StationRepositoryPort = Depends(get_estacao_repository),
    user=Depends(get_current_user)
):
    if upload.content_type not in ("text/plain", "text/csv", "application/vnd.ms-excel"):
        raise HTTPException(status_code=415, detail=f"Tipo de arquivo não suportado: {upload.content_type}")

    data = await upload.read()
    usecase = ImportStationsUseCase(repo)
    report = await usecase.execute(data, encoding="latin1", upsert_existing=upsert_existing)
    return report