from fastapi import APIRouter, Depends, Query
from sqlalchemy import Engine, text

from db import get_engine
from repositories.closures import CLOSED_STATUSES

router = APIRouter(prefix="/closures", tags=["closures"])


@router.get("")
def list_closures(
    idsucursal: int | None = Query(default=None),
    months: int = Query(default=3, ge=1, le=60),
    limit: int = Query(default=50, ge=1, le=500),
    engine: Engine = Depends(get_engine),
):
    sql = """
        SELECT
            i.idinventariomes,
            i.idsucursal,
            i.idalmacen,
            i.idauditor,
            i.idusuario,
            i.inventariomes_fecha AS fecha,
            i.inventariomes_estatus AS estatus,
            i.inventariomes_total AS total,
            i.inventariomes_faltantes AS faltantes,
            i.inventariomes_sobrantes AS sobrantes
        FROM inventariomes i
        WHERE i.inventariomes_estatus IN :statuses
          AND i.inventariomes_fecha >= DATE_SUB(NOW(), INTERVAL :months MONTH)
          {sucursal_clause}
        ORDER BY i.inventariomes_fecha DESC
        LIMIT :limit
    """
    sucursal_clause = "AND i.idsucursal = :idsucursal" if idsucursal is not None else ""
    sql = sql.format(sucursal_clause=sucursal_clause)
    params: dict = {"months": months, "limit": limit}
    if idsucursal is not None:
        params["idsucursal"] = idsucursal

    with engine.connect() as conn:
        result = conn.execute(text(sql).bindparams(statuses=CLOSED_STATUSES), params)
        rows = [dict(r._mapping) for r in result]
    return rows
