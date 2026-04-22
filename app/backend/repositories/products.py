from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine, text

from .closures import CLOSED_STATUSES


def get_product_variance_history(
    engine: Engine, idproducto: int, idsucursal: int, limit: int = 24
) -> pd.DataFrame:
    sql = """
        SELECT
            d.idinventariomes,
            i.inventariomes_fecha      AS fecha,
            d.inventariomesdetalle_diferencia AS diferencia,
            d.inventariomesdetalle_difimporte AS difimporte,
            d.inventariomesdetalle_stockteorico AS stockteorico
        FROM inventariomesdetalle d
        JOIN inventariomes i ON i.idinventariomes = d.idinventariomes
        WHERE d.idproducto = :idproducto
          AND i.idsucursal = :idsucursal
          AND i.inventariomes_estatus IN :statuses
        ORDER BY i.inventariomes_fecha DESC
        LIMIT :limit
    """
    with engine.connect() as conn:
        return pd.read_sql(
            text(sql).bindparams(statuses=CLOSED_STATUSES),
            conn,
            params={"idproducto": idproducto, "idsucursal": idsucursal, "limit": limit},
        )
