"""
queries.py — Capa de consultas SQL reutilizable para el análisis de Cierre de Semana (TALOS).

Uso:
    from sqlalchemy import create_engine
    from src.queries import get_cierre_semana, get_category_summary

    engine = create_engine("mysql+pymysql://root:root@127.0.0.1:3307/talos_tecmty")
    df = get_cierre_semana(engine, idinventariomes=12345)
"""

import pandas as pd
from sqlalchemy import text


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _read_sql(engine, sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


# ---------------------------------------------------------------------------
# Consultas de cierre
# ---------------------------------------------------------------------------

def get_cierre_semana(engine, idinventariomes: int) -> pd.DataFrame:
    """
    Retorna el detalle completo de un Cierre de Semana (todos los productos
    con sus movimientos, stocks y variaciones).

    Columnas clave en el resultado:
        idproducto, producto_nombre, categoria_nombre, subcategoria_nombre,
        unidadmedida_nombre,
        stockinicial, ingresocompra, ingresorequisicion,
        egresoventa, egresorequisicion, egresodevolucion,
        egresoordentablajeria, ingresoordentablajeria, reajuste,
        stockteorico, stockfisico, diferencia,
        costopromedio, difimporte, importefisico,
        aclaracion
    """
    sql = """
        SELECT
            d.idinventariomesdetalle,
            d.idinventariomes,
            d.idproducto,
            p.producto_nombre,
            p.producto_tipo,
            cat.categoria_nombre,
            subcat.categoria_nombre   AS subcategoria_nombre,
            um.unidadmedida_nombre,
            -- Existencias
            d.inventariomesdetalle_stockinicial                   AS stockinicial,
            d.inventariomesdetalle_stockteorico                   AS stockteorico,
            d.inventariomesdetalle_stockfisico                    AS stockfisico,
            d.inventariomesdetalle_diferencia                     AS diferencia,
            -- Movimientos de entrada
            d.inventariomesdetalle_ingresocompra                  AS ingresocompra,
            d.inventariomesdetalle_ingresorequisicion             AS ingresorequisicion,
            d.inventariomesdetalle_ingresoordentablajeria         AS ingresoordentablajeria,
            -- Movimientos de salida
            d.inventariomesdetalle_egresoventa                    AS egresoventa,
            d.inventariomesdetalle_egresorequisicion              AS egresorequisicion,
            d.inventariomesdetalle_egresodevolucion               AS egresodevolucion,
            d.inventariomesdetalle_egresoordentablajeria          AS egresoordentablajeria,
            -- Ajustes
            d.inventariomesdetalle_reajuste                       AS reajuste,
            -- Costos y valores
            d.inventariomesdetalle_costopromedio                  AS costopromedio,
            d.inventariomesdetalle_difimporte                     AS difimporte,
            d.inventariomesdetalle_importefisico                  AS importefisico,
            -- Notas
            d.inventariomesdetalle_aclaracion                     AS aclaracion,
            d.inventariomesdetalle_categoria_aclaracion           AS categoria_aclaracion
        FROM inventariomesdetalle d
        JOIN producto p
            ON p.idproducto = d.idproducto
        JOIN categoria cat
            ON cat.idcategoria = p.idcategoria
        LEFT JOIN categoria subcat
            ON subcat.idcategoria = p.idsubcategoria
        LEFT JOIN unidadmedida um
            ON um.idunidadmedida = p.idunidadmedida
        WHERE d.idinventariomes = :inv_id
        ORDER BY ABS(d.inventariomesdetalle_difimporte) DESC
    """
    return _read_sql(engine, sql, {"inv_id": idinventariomes})


def get_cierre_header(engine, idinventariomes: int) -> pd.DataFrame:
    """
    Retorna el encabezado (resumen financiero) de un Cierre de Semana.
    """
    sql = """
        SELECT
            im.idinventariomes,
            im.idsucursal,
            im.idalmacen,
            im.idempresa,
            im.inventariomes_fecha                  AS fecha,
            im.inventariomes_estatus                AS estatus,
            im.inventariomes_finalalimentos         AS total_alimentos,
            im.inventariomes_finalbebidas           AS total_bebidas,
            im.inventariomes_finalmiscelaneos       AS total_miscelaneos,
            im.inventariomes_faltantes              AS faltantes,
            im.inventariomes_sobrantes              AS sobrantes,
            im.inventariomes_total                  AS neto,
            im.inventariomes_totalimportefisico     AS importe_fisico_total,
            im.inventariomes_version                AS version,
            a.almacen_nombre
        FROM inventariomes im
        LEFT JOIN almacen a ON a.idalmacen = im.idalmacen
        WHERE im.idinventariomes = :inv_id
    """
    return _read_sql(engine, sql, {"inv_id": idinventariomes})


def get_branch_history(
    engine,
    idsucursal: int,
    months: int = 12,
    estatus: tuple = ("finalizado", "aplicado", "terminado"),
) -> pd.DataFrame:
    """
    Retorna los últimos N meses de cierres cerrados para una sucursal.
    Útil para detectar tendencias y patrones recurrentes.
    """
    estatus_placeholders = ", ".join(f":s{i}" for i in range(len(estatus)))
    params = {"sucursal": idsucursal, "months": months}
    for i, s in enumerate(estatus):
        params[f"s{i}"] = s

    sql = f"""
        SELECT
            im.idinventariomes,
            im.idalmacen,
            a.almacen_nombre,
            im.inventariomes_fecha               AS fecha,
            im.inventariomes_estatus             AS estatus,
            im.inventariomes_faltantes           AS faltantes,
            im.inventariomes_sobrantes           AS sobrantes,
            im.inventariomes_total               AS neto,
            im.inventariomes_totalimportefisico  AS importe_fisico_total
        FROM inventariomes im
        LEFT JOIN almacen a ON a.idalmacen = im.idalmacen
        WHERE im.idsucursal = :sucursal
          AND im.inventariomes_estatus IN ({estatus_placeholders})
          AND im.inventariomes_fecha >= DATE_SUB(NOW(), INTERVAL :months MONTH)
        ORDER BY im.inventariomes_fecha DESC
    """
    return _read_sql(engine, sql, params)


def get_product_variance_history(
    engine,
    idproducto: int,
    idsucursal: int | None = None,
    limit: int = 24,
) -> pd.DataFrame:
    """
    Historial de variaciones de un producto a través de múltiples cierres.
    Permite detectar faltantes recurrentes (regla R07).

    Si se proporciona idsucursal, filtra solo esa sucursal.
    """
    sucursal_filter = "AND im.idsucursal = :sucursal" if idsucursal else ""
    params: dict = {"prod": idproducto, "lim": limit}
    if idsucursal:
        params["sucursal"] = idsucursal

    sql = f"""
        SELECT
            d.idinventariomes,
            im.idsucursal,
            im.idalmacen,
            im.inventariomes_fecha      AS fecha,
            d.inventariomesdetalle_diferencia      AS diferencia,
            d.inventariomesdetalle_difimporte      AS difimporte,
            d.inventariomesdetalle_stockteorico    AS stockteorico,
            d.inventariomesdetalle_stockfisico     AS stockfisico,
            d.inventariomesdetalle_costopromedio   AS costopromedio
        FROM inventariomesdetalle d
        JOIN inventariomes im ON im.idinventariomes = d.idinventariomes
        WHERE d.idproducto = :prod
          AND im.inventariomes_estatus IN ('finalizado','aplicado','terminado')
          {sucursal_filter}
        ORDER BY im.inventariomes_fecha DESC
        LIMIT :lim
    """
    return _read_sql(engine, sql, params)


def get_category_summary(engine, idinventariomes: int) -> pd.DataFrame:
    """
    Variación agregada por categoría raíz (Alimentos, Bebidas, Gastos)
    para un Cierre de Semana.

    Columnas: categoria_raiz, n_productos, diferencia_total,
              difimporte_total, difimporte_abs_total, pct_variacion_promedio
    """
    sql = """
        SELECT
            raiz.categoria_nombre                       AS categoria_raiz,
            COUNT(d.idinventariomesdetalle)             AS n_productos,
            SUM(d.inventariomesdetalle_diferencia)      AS diferencia_total,
            SUM(d.inventariomesdetalle_difimporte)      AS difimporte_total,
            SUM(ABS(d.inventariomesdetalle_difimporte)) AS difimporte_abs_total,
            AVG(
                CASE
                    WHEN d.inventariomesdetalle_stockteorico <> 0
                    THEN d.inventariomesdetalle_diferencia
                         / d.inventariomesdetalle_stockteorico * 100
                    ELSE NULL
                END
            )                                           AS pct_variacion_promedio
        FROM inventariomesdetalle d
        JOIN producto p ON p.idproducto = d.idproducto
        JOIN categoria cat ON cat.idcategoria = p.idcategoria
        -- Navegar hasta la categoría raíz (idcategoriapadre IS NULL)
        LEFT JOIN categoria raiz
            ON raiz.idcategoria = (
                SELECT c2.idcategoria
                FROM categoria c2
                WHERE c2.idcategoriapadre IS NULL
                  AND EXISTS (
                      SELECT 1 FROM categoria c3
                      WHERE c3.idcategoria = p.idcategoria
                        AND (
                            c3.idcategoriapadre = c2.idcategoria
                            OR c3.idcategoria = c2.idcategoria
                            OR EXISTS (
                                SELECT 1 FROM categoria c4
                                WHERE c4.idcategoria = c3.idcategoriapadre
                                  AND (c4.idcategoriapadre = c2.idcategoria
                                       OR c4.idcategoria = c2.idcategoria)
                            )
                        )
                )
                LIMIT 1
            )
        WHERE d.idinventariomes = :inv_id
        GROUP BY raiz.categoria_nombre
        ORDER BY difimporte_abs_total DESC
    """
    return _read_sql(engine, sql, {"inv_id": idinventariomes})


def get_category_summary_flat(engine, idinventariomes: int) -> pd.DataFrame:
    """
    Versión simplificada de get_category_summary que usa la categoría directa
    del producto (más eficiente para tablas grandes).
    Incluye categorías de nivel 1 y 2.
    """
    sql = """
        SELECT
            cat.categoria_nombre        AS categoria,
            COUNT(*)                    AS n_lineas,
            SUM(d.inventariomesdetalle_diferencia)      AS diferencia_total,
            SUM(d.inventariomesdetalle_difimporte)      AS difimporte_total,
            SUM(ABS(d.inventariomesdetalle_difimporte)) AS difimporte_abs_total
        FROM inventariomesdetalle d
        JOIN producto p   ON p.idproducto   = d.idproducto
        JOIN categoria cat ON cat.idcategoria = p.idcategoria
        WHERE d.idinventariomes = :inv_id
        GROUP BY cat.idcategoria, cat.categoria_nombre
        ORDER BY difimporte_abs_total DESC
    """
    return _read_sql(engine, sql, {"inv_id": idinventariomes})


def get_sample_closed_inventories(
    engine,
    n: int = 300,
    year_from: int = 2022,
    year_to: int = 2025,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Muestra aleatoria de N cierres completados en un rango de años.
    Se usa en la validación histórica (notebook 4).
    """
    sql = """
        SELECT
            im.idinventariomes,
            im.idsucursal,
            im.idalmacen,
            im.idempresa,
            im.inventariomes_fecha               AS fecha,
            im.inventariomes_faltantes           AS faltantes,
            im.inventariomes_sobrantes           AS sobrantes,
            im.inventariomes_total               AS neto
        FROM inventariomes im
        WHERE im.inventariomes_estatus IN ('finalizado', 'aplicado', 'terminado')
          AND YEAR(im.inventariomes_fecha) BETWEEN :yr_from AND :yr_to
        ORDER BY RAND(:seed)
        LIMIT :n
    """
    return _read_sql(engine, sql, {"n": n, "yr_from": year_from, "yr_to": year_to, "seed": seed})


def get_thresholds_by_category(engine, year_from: int = 2022) -> pd.DataFrame:
    """
    Agrega estadísticos de difimporte por categoría para calibración de umbrales.
    Retorna media, std y max. Para percentiles reales usa get_difimporte_sample_by_category().
    """
    sql = """
        SELECT
            cat.categoria_nombre                                AS categoria,
            COUNT(*)                                            AS n,
            AVG(ABS(d.inventariomesdetalle_difimporte))        AS media_abs_difimporte,
            MAX(ABS(d.inventariomesdetalle_difimporte))        AS max_abs_difimporte,
            STDDEV(d.inventariomesdetalle_difimporte)          AS std_difimporte,
            AVG(d.inventariomesdetalle_difimporte)             AS media_difimporte
        FROM inventariomesdetalle d
        JOIN inventariomes im ON im.idinventariomes = d.idinventariomes
        JOIN producto p       ON p.idproducto       = d.idproducto
        JOIN categoria cat    ON cat.idcategoria    = p.idcategoria
        WHERE im.inventariomes_estatus IN ('finalizado','aplicado','terminado')
          AND YEAR(im.inventariomes_fecha) >= :yr_from
          AND d.inventariomesdetalle_difimporte IS NOT NULL
        GROUP BY cat.idcategoria, cat.categoria_nombre
        ORDER BY n DESC
        LIMIT 50
    """
    return _read_sql(engine, sql, {"yr_from": year_from})


def get_difimporte_sample_by_category(
    engine,
    year_from: int = 2022,
    rows_per_category: int = 8_000,
) -> pd.DataFrame:
    """
    Retorna una muestra aleatoria de valores `difimporte` por categoría de producto,
    de modo que pandas pueda calcular percentiles reales (p90, p95, p99).

    Usar en lugar de mean±std para calibrar umbrales robustos a outliers.

    Args:
        rows_per_category: máximo de filas muestreadas por categoría.
                           8 000 es suficiente para percentiles estables (±1%).

    Returns:
        DataFrame con columnas: categoria, difimporte
    """
    # Tomamos una muestra uniforme usando RAND() sobre cierres cerrados recientes.
    # Limitar por categoría evita que Alimentos (mayor volumen) domine la muestra.
    sql = """
        SELECT
            cat.categoria_nombre  AS categoria,
            d.inventariomesdetalle_difimporte AS difimporte
        FROM (
            SELECT
                d2.inventariomesdetalle_difimporte,
                d2.idproducto,
                ROW_NUMBER() OVER (
                    PARTITION BY p2.idcategoria
                    ORDER BY RAND(:seed)
                ) AS rn
            FROM inventariomesdetalle d2
            JOIN inventariomes im2 ON im2.idinventariomes = d2.idinventariomes
            JOIN producto p2       ON p2.idproducto       = d2.idproducto
            WHERE im2.inventariomes_estatus IN ('finalizado','aplicado','terminado')
              AND YEAR(im2.inventariomes_fecha) >= :yr_from
              AND d2.inventariomesdetalle_difimporte IS NOT NULL
              AND d2.inventariomesdetalle_difimporte <> 0
        ) d
        JOIN producto p   ON p.idproducto   = d.idproducto
        JOIN categoria cat ON cat.idcategoria = p.idcategoria
        WHERE d.rn <= :rpc
    """
    return _read_sql(
        engine, sql,
        {"yr_from": year_from, "rpc": rows_per_category, "seed": 42},
    )


def compute_percentile_thresholds(
    df_sample: pd.DataFrame,
    faltante_alto_q: float = 0.90,
    faltante_critico_q: float = 0.95,
) -> dict:
    """
    Calcula umbrales de alerta por categoría usando percentiles sobre la muestra
    de difimporte devuelta por get_difimporte_sample_by_category().

    Lógica:
      - faltante_alto    = -(percentil faltante_alto_q   de los valores negativos)
      - faltante_critico = -(percentil faltante_critico_q de los valores negativos)
      - sobrante_alto    =   percentil faltante_alto_q   de los valores positivos

    Args:
        df_sample:          DataFrame con columnas 'categoria' y 'difimporte'.
        faltante_alto_q:    Cuantil para umbral ALTA  (default 0.90 → p90).
        faltante_critico_q: Cuantil para umbral CRITICA (default 0.95 → p95).

    Returns:
        Diccionario compatible con DEFAULT_THRESHOLDS en rules.py.
    """
    thresholds: dict = {}

    for cat, grp in df_sample.groupby("categoria"):
        neg = grp.loc[grp["difimporte"] < 0, "difimporte"].abs()
        pos = grp.loc[grp["difimporte"] > 0, "difimporte"]

        if len(neg) < 30 or len(pos) < 30:
            # Muestra insuficiente; se usará _default
            continue

        thresholds[cat] = {
            "faltante_critico": -float(neg.quantile(faltante_critico_q)),
            "faltante_alto":    -float(neg.quantile(faltante_alto_q)),
            "sobrante_alto":     float(pos.quantile(faltante_alto_q)),
        }

    # Fallback global con todos los datos
    neg_all = df_sample.loc[df_sample["difimporte"] < 0, "difimporte"].abs()
    pos_all = df_sample.loc[df_sample["difimporte"] > 0, "difimporte"]
    thresholds["_default"] = {
        "faltante_critico": -float(neg_all.quantile(faltante_critico_q)) if len(neg_all) > 30 else -3_000,
        "faltante_alto":    -float(neg_all.quantile(faltante_alto_q))    if len(neg_all) > 30 else -800,
        "sobrante_alto":     float(pos_all.quantile(faltante_alto_q))    if len(pos_all) > 30 else 800,
    }

    return thresholds
