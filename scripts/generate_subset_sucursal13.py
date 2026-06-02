#!/usr/bin/env python3
"""
generate_subset_sucursal13.py

Produces data/talos_tecmty/subset_sucursal13.sql — a self-contained MySQL seed
file for Sucursal 13 only, suitable for Railway deployment.

Includes:
  - All 7 original tables scoped to sucursal 13
  - requisicion_traspaso: derived inter-almacen transfer records
  - requisicion_traspaso_resumen: aggregated version for dashboards
  - v_consolidado_sucursal13: view that nets out internal transfers

Usage:
    python scripts/generate_subset_sucursal13.py
"""

import math
import sys
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DB_URL = "mysql+pymysql://root:root@127.0.0.1:3307/talos_tecmty"
SUCURSAL_ID = 13
BATCH_SIZE = 500
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "data" / "talos_tecmty" / "subset_sucursal13.sql"
)
SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "app" / "backend" / "schema.sql"
)

engine = create_engine(DB_URL, pool_pre_ping=True)


def read_sql(sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


# ---------------------------------------------------------------------------
# SQL value formatter
# ---------------------------------------------------------------------------

def fmt(v) -> str:
    """Convert a Python / pandas value to a MySQL literal string."""
    # Guard: catch all null-like values first (None, NaN, NaT, pd.NA)
    try:
        if pd.isna(v):
            return "NULL"
    except (TypeError, ValueError):
        pass

    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (np.bool_,)):
        return "1" if bool(v) else "0"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, (float, np.floating)):
        if math.isnan(v) or math.isinf(v):
            return "NULL"
        # Avoid scientific notation
        return f"{v:.6f}".rstrip("0").rstrip(".") or "0"
    if isinstance(v, (pd.Timestamp, datetime)):
        try:
            return f"'{v.strftime('%Y-%m-%d %H:%M:%S')}'"
        except (ValueError, OSError, AttributeError):
            return "NULL"
    if isinstance(v, date):
        return f"'{v.strftime('%Y-%m-%d')}'"
    # String / bytes
    s = str(v)
    s = (
        s.replace("\\", "\\\\")
         .replace("'", "\\'")
         .replace("\0", "\\0")
         .replace("\n", "\\n")
         .replace("\r", "\\r")
    )
    return f"'{s}'"


def df_to_inserts(df: pd.DataFrame, table: str, batch: int = BATCH_SIZE) -> str:
    """Return batched INSERT statements for a DataFrame."""
    if df.empty:
        return f"-- (no rows for {table})\n"
    cols = ", ".join(f"`{c}`" for c in df.columns)
    blocks = []
    for i in range(0, len(df), batch):
        chunk = df.iloc[i : i + batch]
        rows = []
        for tup in chunk.itertuples(index=False, name=None):
            row_vals = ", ".join(fmt(v) for v in tup)
            rows.append(f"  ({row_vals})")
        blocks.append(
            f"INSERT INTO `{table}` ({cols}) VALUES\n"
            + ",\n".join(rows)
            + ";\n"
        )
    return "\n".join(blocks)


# ---------------------------------------------------------------------------
# Schema definitions for new derived tables
# ---------------------------------------------------------------------------

NEW_TABLES_SQL = """
-- ---------------------------------------------------------------------------
-- Derived table: inter-almacen transfer records (traspaso entre almacenes)
-- Origin + destination in one row. Derived from ingresorequisicion /
-- egresorequisicion columns via proportional waterfall matching.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS `requisicion_traspaso`;
CREATE TABLE `requisicion_traspaso` (
  `idrequisicion_traspaso`  INT          NOT NULL AUTO_INCREMENT,
  `idsucursal`              INT          NOT NULL,
  `idalmacen_origen`        INT          NOT NULL COMMENT 'almacen that dispatched (egresorequisicion)',
  `idalmacen_destino`       INT          NOT NULL COMMENT 'almacen that received (ingresorequisicion)',
  `idproducto`              INT          NOT NULL,
  `idinventariomes_origen`  INT          NOT NULL,
  `idinventariomes_destino` INT          NOT NULL,
  `fecha_cierre`            DATETIME     NOT NULL,
  `cantidad`                DECIMAL(15,6) NOT NULL,
  PRIMARY KEY (`idrequisicion_traspaso`),
  KEY `idx_rt_suc`   (`idsucursal`),
  KEY `idx_rt_prod`  (`idproducto`),
  KEY `idx_rt_fecha` (`fecha_cierre`),
  KEY `idx_rt_origen`   (`idalmacen_origen`),
  KEY `idx_rt_destino`  (`idalmacen_destino`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- ---------------------------------------------------------------------------
-- Derived table: aggregated traspaso (no product detail) for fast queries
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS `requisicion_traspaso_resumen`;
CREATE TABLE `requisicion_traspaso_resumen` (
  `idsucursal`        INT          NOT NULL,
  `idalmacen_origen`  INT          NOT NULL,
  `idalmacen_destino` INT          NOT NULL,
  `fecha_cierre`      DATETIME     NOT NULL,
  `total_unidades`    DECIMAL(15,6) NOT NULL,
  `num_productos`     INT          NOT NULL,
  PRIMARY KEY (`idsucursal`, `idalmacen_origen`, `idalmacen_destino`, `fecha_cierre`),
  KEY `idx_rtr_suc`   (`idsucursal`),
  KEY `idx_rtr_fecha` (`fecha_cierre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
"""

CONSOLIDADO_VIEW_SQL = """
-- ---------------------------------------------------------------------------
-- View: restaurant-level consolidado (all almacenes aggregated).
-- ingresorequisicion / egresorequisicion are kept for audit but cancel at
-- restaurant level — only ingresocompra represents real external purchases.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS `v_consolidado_sucursal13`;
CREATE VIEW `v_consolidado_sucursal13` AS
SELECT
    im.inventariomes_fecha                                  AS fecha,
    im.idsucursal,
    imd.idproducto,
    p.producto_nombre,
    cat.categoria_nombre,
    SUM(imd.inventariomesdetalle_stockinicial)              AS stockinicial,
    SUM(imd.inventariomesdetalle_stockteorico)              AS stockteorico,
    SUM(imd.inventariomesdetalle_stockfisico)               AS stockfisico,
    SUM(imd.inventariomesdetalle_diferencia)                AS diferencia,
    SUM(imd.inventariomesdetalle_ingresocompra)             AS ingresocompra,
    SUM(imd.inventariomesdetalle_ingresorequisicion)        AS ingreso_req_interno,
    SUM(imd.inventariomesdetalle_egresorequisicion)         AS egreso_req_interno,
    SUM(imd.inventariomesdetalle_egresoventa)               AS egresoventa,
    SUM(imd.inventariomesdetalle_reajuste)                  AS reajuste,
    SUM(imd.inventariomesdetalle_ingresoordentablajeria)    AS ingresoordentablajeria,
    SUM(imd.inventariomesdetalle_egresoordentablajeria)     AS egresoordentablajeria,
    SUM(imd.inventariomesdetalle_egresodevolucion)          AS egresodevolucion,
    SUM(imd.inventariomesdetalle_difimporte)                AS difimporte,
    SUM(imd.inventariomesdetalle_importefisico)             AS importefisico
FROM inventariomesdetalle imd
JOIN inventariomes im  ON im.idinventariomes = imd.idinventariomes
JOIN producto p        ON p.idproducto       = imd.idproducto
JOIN categoria cat     ON cat.idcategoria    = p.idcategoria
WHERE im.idsucursal = 13
GROUP BY
    im.inventariomes_fecha,
    im.idsucursal,
    imd.idproducto,
    p.producto_nombre,
    cat.categoria_nombre;
"""


# ---------------------------------------------------------------------------
# Requisicion derivation
# ---------------------------------------------------------------------------

def derive_requisicion_traspaso() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    For each (fecha_cierre, idproducto) in sucursal 13, match almacenes that
    sent (egresorequisicion > 0) to almacenes that received (ingresorequisicion > 0)
    using a proportional waterfall algorithm.

    Returns (traspaso_df, resumen_df).
    """
    print("  Loading non-zero requisicion rows...", flush=True)
    req = read_sql("""
        SELECT
            im.idinventariomes,
            im.idalmacen,
            im.inventariomes_fecha                              AS fecha,
            imd.idproducto,
            CAST(imd.inventariomesdetalle_egresorequisicion  AS DECIMAL(15,6)) AS egreso,
            CAST(imd.inventariomesdetalle_ingresorequisicion AS DECIMAL(15,6)) AS ingreso
        FROM inventariomesdetalle imd
        JOIN inventariomes im ON im.idinventariomes = imd.idinventariomes
        WHERE im.idsucursal = :suc
          AND (imd.inventariomesdetalle_egresorequisicion  > 0
            OR imd.inventariomesdetalle_ingresorequisicion > 0)
    """, {"suc": SUCURSAL_ID})

    req["egreso"]  = req["egreso"].astype(float)
    req["ingreso"] = req["ingreso"].astype(float)

    print(f"  {len(req):,} rows with non-zero requisicion. Building traspaso records...", flush=True)

    records = []
    groups = req.groupby(["fecha", "idproducto"])
    total = len(groups)

    for idx, ((fecha, idprod), grp) in enumerate(groups):
        if idx % 5000 == 0:
            print(f"    {idx:,}/{total:,} groups processed...", end="\r", flush=True)

        senders   = grp[grp["egreso"]  > 1e-6][["idalmacen", "idinventariomes", "egreso"]].copy()
        receivers = grp[grp["ingreso"] > 1e-6][["idalmacen", "idinventariomes", "ingreso"]].copy()

        if senders.empty or receivers.empty:
            continue

        senders   = senders.sort_values("egreso",  ascending=False).reset_index(drop=True)
        receivers = receivers.sort_values("ingreso", ascending=False).reset_index(drop=True)

        s_rem = senders["egreso"].tolist()
        r_rem = receivers["ingreso"].tolist()
        s_alm = senders["idalmacen"].tolist()
        r_alm = receivers["idalmacen"].tolist()
        s_inv = senders["idinventariomes"].tolist()
        r_inv = receivers["idinventariomes"].tolist()

        si, ri = 0, 0
        while si < len(s_rem) and ri < len(r_rem):
            amount = min(s_rem[si], r_rem[ri])
            if amount > 1e-6:
                records.append({
                    "idsucursal":              SUCURSAL_ID,
                    "idalmacen_origen":        s_alm[si],
                    "idalmacen_destino":       r_alm[ri],
                    "idproducto":              idprod,
                    "idinventariomes_origen":  s_inv[si],
                    "idinventariomes_destino": r_inv[ri],
                    "fecha_cierre":            fecha,
                    "cantidad":                round(amount, 6),
                })
            s_rem[si] -= amount
            r_rem[ri] -= amount
            if s_rem[si] < 1e-6:
                si += 1
            if r_rem[ri] < 1e-6:
                ri += 1

    print(f"\n  Generated {len(records):,} traspaso records.", flush=True)

    if not records:
        return pd.DataFrame(), pd.DataFrame()

    traspaso_df = pd.DataFrame(records)

    # Build resumen
    resumen_df = (
        traspaso_df
        .groupby(["idsucursal", "idalmacen_origen", "idalmacen_destino", "fecha_cierre"])
        .agg(total_unidades=("cantidad", "sum"), num_productos=("idproducto", "nunique"))
        .reset_index()
    )
    resumen_df["total_unidades"] = resumen_df["total_unidades"].round(6)

    return traspaso_df, resumen_df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print(f"Generating subset for sucursal {SUCURSAL_ID}")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 60)

    lines: list[str] = []

    def section(title: str):
        lines.append(f"\n-- {'=' * 60}")
        lines.append(f"-- {title}")
        lines.append(f"-- {'=' * 60}\n")

    # Header
    lines.append(f"-- subset_sucursal13.sql")
    lines.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"-- Sucursal: {SUCURSAL_ID} | Tables: 7 original + 2 derived | View: 1")
    lines.append("-- Load: mysql -uroot -proot <db> < subset_sucursal13.sql\n")
    lines.append("SET NAMES utf8mb4;")
    lines.append("SET FOREIGN_KEY_CHECKS = 0;")
    lines.append("SET UNIQUE_CHECKS = 0;")
    lines.append("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';\n")

    # ------------------------------------------------------------------ #
    # 0. Schema (CREATE TABLE for all original tables)
    # ------------------------------------------------------------------ #
    section("Schema — original 7 tables")
    print("Embedding schema DDL...", flush=True)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    # Strip the outer SET commands (we already emit them above) and keep
    # only the DROP/CREATE statements.
    schema_lines = []
    skip_prefixes = ("SET NAMES", "SET FOREIGN_KEY_CHECKS", "SET UNIQUE_CHECKS", "SET SQL_MODE")
    for sl in schema_sql.splitlines():
        if any(sl.strip().startswith(p) for p in skip_prefixes):
            continue
        schema_lines.append(sl)
    lines.append("\n".join(schema_lines))

    # ------------------------------------------------------------------ #
    # 1. Reference tables (full, small)
    # ------------------------------------------------------------------ #
    for tbl in ("unidadmedida", "categoria"):
        section(f"Table: {tbl}")
        print(f"Loading {tbl}...", flush=True)
        df = read_sql(f"SELECT * FROM `{tbl}`")
        lines.append(df_to_inserts(df, tbl))
        print(f"  → {len(df):,} rows")

    # ------------------------------------------------------------------ #
    # 2. Almacenes for sucursal 13
    # ------------------------------------------------------------------ #
    section("Table: almacen (sucursal 13 only)")
    print("Loading almacen...", flush=True)
    df_alm = read_sql("SELECT * FROM almacen WHERE idsucursal = :s", {"s": SUCURSAL_ID})
    lines.append(df_to_inserts(df_alm, "almacen"))
    print(f"  → {len(df_alm):,} rows")

    # ------------------------------------------------------------------ #
    # 3. Productos referenced by sucursal 13 inventories
    # ------------------------------------------------------------------ #
    section("Table: producto (only products used in sucursal 13)")
    print("Loading producto...", flush=True)
    df_prod = read_sql("""
        SELECT DISTINCT p.*
        FROM producto p
        JOIN inventariomesdetalle imd ON imd.idproducto = p.idproducto
        JOIN inventariomes im         ON im.idinventariomes = imd.idinventariomes
        WHERE im.idsucursal = :s
    """, {"s": SUCURSAL_ID})
    lines.append(df_to_inserts(df_prod, "producto"))
    print(f"  → {len(df_prod):,} rows")

    # productotalos — only those referenced by the productos we selected
    section("Table: productotalos (referenced by sucursal 13 products)")
    print("Loading productotalos...", flush=True)
    pt_ids = df_prod["idproductotalos"].dropna().astype(int).unique().tolist()
    if pt_ids:
        placeholders = ", ".join(str(i) for i in pt_ids)
        df_pt = read_sql(f"SELECT * FROM productotalos WHERE idproductotalos IN ({placeholders})")
    else:
        df_pt = pd.DataFrame()
    lines.append(df_to_inserts(df_pt, "productotalos"))
    print(f"  → {len(df_pt):,} rows")

    # ------------------------------------------------------------------ #
    # 4. inventariomes for sucursal 13
    # ------------------------------------------------------------------ #
    section("Table: inventariomes (sucursal 13 only)")
    print("Loading inventariomes...", flush=True)
    df_im = read_sql("SELECT * FROM inventariomes WHERE idsucursal = :s", {"s": SUCURSAL_ID})
    lines.append(df_to_inserts(df_im, "inventariomes"))
    print(f"  → {len(df_im):,} rows")

    # ------------------------------------------------------------------ #
    # 5. inventariomesdetalle (largest table — batch load)
    # ------------------------------------------------------------------ #
    section("Table: inventariomesdetalle (sucursal 13 only, batched)")
    print("Loading inventariomesdetalle (this may take a minute)...", flush=True)
    df_det = read_sql("""
        SELECT imd.*
        FROM inventariomesdetalle imd
        JOIN inventariomes im ON im.idinventariomes = imd.idinventariomes
        WHERE im.idsucursal = :s
    """, {"s": SUCURSAL_ID})
    lines.append(df_to_inserts(df_det, "inventariomesdetalle", batch=500))
    print(f"  → {len(df_det):,} rows")

    # ------------------------------------------------------------------ #
    # 6. Derived tables: requisicion_traspaso
    # ------------------------------------------------------------------ #
    section("Derived tables: requisicion_traspaso + requisicion_traspaso_resumen")
    print("Creating derived tables schema...", flush=True)
    lines.append(NEW_TABLES_SQL)

    print("Deriving traspaso records...", flush=True)
    df_traspaso, df_resumen = derive_requisicion_traspaso()

    if not df_traspaso.empty:
        lines.append(df_to_inserts(df_traspaso, "requisicion_traspaso", batch=500))
        print(f"  → {len(df_traspaso):,} traspaso rows")
    if not df_resumen.empty:
        lines.append(df_to_inserts(df_resumen, "requisicion_traspaso_resumen", batch=500))
        print(f"  → {len(df_resumen):,} resumen rows")

    # ------------------------------------------------------------------ #
    # 7. Consolidado view
    # ------------------------------------------------------------------ #
    section("View: v_consolidado_sucursal13")
    lines.append(CONSOLIDADO_VIEW_SQL)

    # ------------------------------------------------------------------ #
    # Footer
    # ------------------------------------------------------------------ #
    lines.append("\nSET UNIQUE_CHECKS = 1;")
    lines.append("SET FOREIGN_KEY_CHECKS = 1;\n")
    lines.append("-- Validation queries")
    lines.append("-- SELECT COUNT(*) AS inventariomes       FROM inventariomes;")
    lines.append("-- SELECT COUNT(*) AS inventariomesdetalle FROM inventariomesdetalle;")
    lines.append("-- SELECT COUNT(*) AS requisicion_traspaso FROM requisicion_traspaso;")
    lines.append("-- SELECT COUNT(*) AS resumen              FROM requisicion_traspaso_resumen;")

    # ------------------------------------------------------------------ #
    # Write file
    # ------------------------------------------------------------------ #
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nWriting SQL file to {OUTPUT_PATH}...", flush=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    size_mb = OUTPUT_PATH.stat().st_size / 1_048_576
    print(f"Done. File size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
