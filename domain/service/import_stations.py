from typing import Dict, Any, List
from unidecode import unidecode

from domain.models.station_model import StationModel
from domain.ports.station_repository_port import StationRepositoryPort


class ImportStationsUseCase:
    MIN_COLS = 6  # ponto, codigo_estacao, id_noaa, conversor, sensor, bacia

    def __init__(self, repo: StationRepositoryPort):
        self._repo = repo

    async def execute(
        self,
        file_bytes: bytes,
        encoding: str = "latin1",
        upsert_existing: bool = False,  # <— novo
    ) -> Dict[str, Any]:

        text = file_bytes.decode(encoding, errors="replace")

        imported: int = 0
        ignored: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        estacoes_validas: List[StationModel] = []

        # pré-carrega códigos existentes (para decidir ignorar ou não)
        try:
            existentes = {e.codigo_estacao for e in self._repo.list_all_stations()}
        except Exception as ex:
            existentes = set()
            errors.append({"line": 0, "error": f"falha ao listar existentes: {ex}", "content": ""})

        seen_in_file: set[str] = set()

        for num, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split(",")]

            # 1) header? (robusto nos dois cenários)
            if num == 1 and parts and parts[0].lower() == "ponto":
                # pula cabeçalho
                continue

            if len(parts) < self.MIN_COLS:
                ignored.append({"line": num, "reason": f"{len(parts)} colunas (< {self.MIN_COLS})", "content": line})
                continue

            try:
                ponto     = unidecode(parts[0])
                codigo    = parts[1]
                id_noaa   = parts[2]

                # 2) garante int para 'conversor'
                try:
                    conversor_val = int(parts[3])
                except ValueError as ve:
                    raise ValueError(f"conversor inválido (não é int): {parts[3]}") from ve

                sensor    = unidecode(parts[4])
                bacia     = unidecode(parts[5])
                if len(parts) >= 7 and parts[6]:
                    bacia = unidecode(parts[6])

                # 3) duplicado no arquivo
                if codigo in seen_in_file:
                    ignored.append({"line": num, "reason": "duplicado no arquivo (codigo_estacao)", "content": line})
                    continue
                seen_in_file.add(codigo)

                # 4) já existe no banco → ignora (default) OU permite upsert
                if not upsert_existing and codigo in existentes:
                    ignored.append({"line": num, "reason": "duplicado no banco (codigo_estacao)", "content": line})
                    continue

                estacoes_validas.append(
                    StationModel(
                        ponto=ponto,
                        codigo_estacao=codigo,
                        id_noaa=id_noaa,
                        conversor=conversor_val,  # agora int
                        sensor=sensor,
                        bacia=bacia,
                    )
                )
            except Exception as ex:
                errors.append({"line": num, "error": str(ex), "content": line})

        if estacoes_validas:
            imported = self._repo.save_many(estacoes_validas)

        return {
            "imported": imported,
            "ignored": ignored,
            "errors": errors,
            "summary": {
                "total_lines": len(text.splitlines()),
                "processed": imported + len(ignored) + len(errors),
            },
        }
