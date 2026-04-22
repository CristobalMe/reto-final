from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine, text

from .closures import CLOSED_STATUSES


def get_auditor_stats_for_branch(
    engine: Engine, idsucursal: int, months: int = 12
) -> pd.DataFrame:
    """Per-auditor aggregate stats across a branch's recent closed closures."""
    sql = """
        SELECT
            i.idauditor,
            COUNT(*)                                        AS closures_count,
            SUM(i.inventariomes_faltantes)                  AS total_faltantes,
            SUM(i.inventariomes_sobrantes)                  AS total_sobrantes,
            AVG(i.inventariomes_faltantes)                  AS avg_faltantes,
            AVG(i.inventariomes_total)                      AS avg_total,
            SUM(CASE WHEN i.idauditor = i.idusuario THEN 1 ELSE 0 END) AS self_closures
        FROM inventariomes i
        WHERE i.idsucursal = :idsucursal
          AND i.inventariomes_estatus IN :statuses
          AND i.inventariomes_fecha >= DATE_SUB(NOW(), INTERVAL :months MONTH)
          AND i.idauditor IS NOT NULL
        GROUP BY i.idauditor
    """
    with engine.connect() as conn:
        return pd.read_sql(
            text(sql).bindparams(statuses=CLOSED_STATUSES),
            conn,
            params={"idsucursal": idsucursal, "months": months},
        )
