from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine, text

CLOSED_STATUSES = ("finalizado", "aplicado", "terminado")


def _read(engine: Engine, sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def get_closure_header(engine: Engine, idinventariomes: int) -> pd.DataFrame:
    sql = """
        SELECT
            i.idinventariomes,
            i.idsucursal,
            i.idalmacen,
            i.idauditor,
            i.idusuario,
            i.inventariomes_fecha          AS fecha,
            i.inventariomes_estatus        AS estatus,
            i.inventariomes_total          AS total,
            i.inventariomes_faltantes      AS faltantes,
            i.inventariomes_sobrantes      AS sobrantes,
            i.inventariomes_totalimportefisico AS total_fisico,
            i.inventariomes_finalalimentos AS final_alimentos,
            i.inventariomes_finalbebidas   AS final_bebidas,
            i.inventariomes_finalmiscelaneos AS final_miscelaneos,
            a.almacen_nombre                AS almacen_nombre,
            a.almacen_encargado             AS almacen_encargado
        FROM inventariomes i
        LEFT JOIN almacen a ON a.idalmacen = i.idalmacen
        WHERE i.idinventariomes = :id
    """
    return _read(engine, sql, {"id": idinventariomes})


def get_closure_detail(engine: Engine, idinventariomes: int) -> pd.DataFrame:
    """All line items for a closure, joined with product + category + unit."""
    sql = """
        SELECT
            d.idinventariomesdetalle,
            d.idinventariomes,
            d.idproducto,
            p.producto_nombre,
            p.producto_tipo,
            p.clase_clave                                       AS producto_clase,
            p.producto_costo                                    AS producto_costo_ref,
            p.producto_ultimocosto                              AS producto_ultimocosto,
            cat_root.categoria_nombre                           AS categoria_nombre,
            cat.categoria_nombre                                AS subcategoria_nombre,
            um.unidadmedida_nombre,
            d.inventariomesdetalle_stockinicial                 AS stockinicial,
            d.inventariomesdetalle_stockteorico                 AS stockteorico,
            d.inventariomesdetalle_stockfisico                  AS stockfisico,
            d.inventariomesdetalle_totalfisico                  AS totalfisico,
            d.inventariomesdetalle_diferencia                   AS diferencia,
            d.inventariomesdetalle_ingresocompra                AS ingresocompra,
            d.inventariomesdetalle_ingresorequisicion           AS ingresorequisicion,
            d.inventariomesdetalle_egresorequisicion            AS egresorequisicion,
            d.inventariomesdetalle_egresoventa                  AS egresoventa,
            d.inventariomesdetalle_reajuste                     AS reajuste,
            d.inventariomesdetalle_ingresoordentablajeria       AS ingresoordentablajeria,
            d.inventariomesdetalle_egresoordentablajeria        AS egresoordentablajeria,
            d.inventariomesdetalle_egresodevolucion             AS egresodevolucion,
            d.inventariomesdetalle_costopromedio                AS costopromedio,
            d.inventariomesdetalle_difimporte                   AS difimporte,
            d.inventariomesdetalle_importefisico                AS importefisico,
            d.inventariomesdetalle_aclaracion                   AS aclaracion,
            d.inventariomesdetalle_revisada                     AS revisada
        FROM inventariomesdetalle d
        JOIN producto p                ON p.idproducto = d.idproducto
        LEFT JOIN categoria cat        ON cat.idcategoria = p.idcategoria
        LEFT JOIN categoria cat_root   ON cat_root.idcategoria = COALESCE(cat.idcategoriapadre, cat.idcategoria)
        LEFT JOIN unidadmedida um      ON um.idunidadmedida = p.idunidadmedida
        WHERE d.idinventariomes = :id
    """
    df = _read(engine, sql, {"id": idinventariomes})
    _coerce_numeric(df)
    return df


def list_closures_for_branch(
    engine: Engine, idsucursal: int, months: int = 12
) -> pd.DataFrame:
    sql = """
        SELECT
            i.idinventariomes,
            i.idsucursal,
            i.idalmacen,
            i.idauditor,
            i.idusuario,
            i.inventariomes_fecha     AS fecha,
            i.inventariomes_estatus   AS estatus,
            i.inventariomes_total     AS total,
            i.inventariomes_faltantes AS faltantes,
            i.inventariomes_sobrantes AS sobrantes,
            i.inventariomes_totalimportefisico AS total_fisico
        FROM inventariomes i
        WHERE i.idsucursal = :idsucursal
          AND i.inventariomes_estatus IN :statuses
          AND i.inventariomes_fecha >= DATE_SUB(NOW(), INTERVAL :months MONTH)
        ORDER BY i.inventariomes_fecha DESC
    """
    with engine.connect() as conn:
        return pd.read_sql(
            text(sql).bindparams(
                statuses=CLOSED_STATUSES,  # expanded by SQLAlchemy
            ).execution_options(),
            conn,
            params={"idsucursal": idsucursal, "months": months},
        )


def get_branch_detail_history(
    engine: Engine,
    idsucursal: int,
    months: int = 12,
    limit_rows: int = 200_000,
) -> pd.DataFrame:
    """Detail rows across all recent closed closures for a branch.

    Limited to keep historical endpoints snappy; expand in a repo method if
    you need exhaustive data.
    """
    sql = """
        SELECT
            d.idinventariomes,
            d.idproducto,
            p.producto_nombre,
            cat_root.categoria_nombre AS categoria_nombre,
            i.inventariomes_fecha     AS fecha,
            i.idauditor,
            d.inventariomesdetalle_stockteorico AS stockteorico,
            d.inventariomesdetalle_stockfisico  AS stockfisico,
            d.inventariomesdetalle_diferencia   AS diferencia,
            d.inventariomesdetalle_difimporte   AS difimporte,
            d.inventariomesdetalle_costopromedio AS costopromedio
        FROM inventariomesdetalle d
        JOIN inventariomes i       ON i.idinventariomes = d.idinventariomes
        JOIN producto p            ON p.idproducto = d.idproducto
        LEFT JOIN categoria cat    ON cat.idcategoria = p.idcategoria
        LEFT JOIN categoria cat_root ON cat_root.idcategoria = COALESCE(cat.idcategoriapadre, cat.idcategoria)
        WHERE i.idsucursal = :idsucursal
          AND i.inventariomes_estatus IN :statuses
          AND i.inventariomes_fecha >= DATE_SUB(NOW(), INTERVAL :months MONTH)
        ORDER BY i.inventariomes_fecha DESC
        LIMIT :limit_rows
    """
    with engine.connect() as conn:
        df = pd.read_sql(
            text(sql).bindparams(statuses=CLOSED_STATUSES),
            conn,
            params={"idsucursal": idsucursal, "months": months, "limit_rows": limit_rows},
        )
    _coerce_numeric(df)
    return df


def _coerce_numeric(df: pd.DataFrame) -> None:
    numeric_cols = [
        "stockinicial", "stockteorico", "stockfisico", "totalfisico",
        "diferencia", "ingresocompra", "ingresorequisicion",
        "egresorequisicion", "egresoventa", "reajuste",
        "ingresoordentablajeria", "egresoordentablajeria", "egresodevolucion",
        "costopromedio", "difimporte", "importefisico",
        "producto_costo_ref", "producto_ultimocosto",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
