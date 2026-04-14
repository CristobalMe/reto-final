"""
scoring.py — Motor de priorización de hallazgos del Cierre de Semana (TALOS).

Convierte la lista de alertas de rules.py en un ranking ordenado por impacto,
facilitando que el auditor enfoque su atención en los hallazgos más críticos primero.

Uso:
    from src.scoring import score_and_rank

    df_ranked = score_and_rank(alerts, df_history_counts=recurrence_df)
"""

from __future__ import annotations

import math
import pandas as pd
from src.rules import Alert, alerts_to_dataframe


# ---------------------------------------------------------------------------
# Mapas de pesos
# ---------------------------------------------------------------------------

SEVERITY_SCORE: dict[str, int] = {
    "CRITICA": 4,
    "ALTA":    3,
    "MEDIA":   2,
    "BAJA":    1,
}

# Pesos del score compuesto (ajustables)
# El impacto monetario domina; la severidad y recurrencia son multiplicadores.
WEIGHTS = {
    "w_mxn":        0.70,   # peso del impacto monetario normalizado
    "w_severity":   0.20,   # peso del nivel de severidad
    "w_recurrence": 0.10,   # peso de la recurrencia histórica
}

# Factor máximo de recurrencia (cap para no distorsionar el ranking)
MAX_RECURRENCE_FACTOR = 3.0


# ---------------------------------------------------------------------------
# Normalización
# ---------------------------------------------------------------------------

def _normalize_series(s: pd.Series) -> pd.Series:
    """Min-max normalization; devuelve 0 si todos los valores son iguales."""
    rng = s.max() - s.min()
    if rng == 0:
        return pd.Series([0.5] * len(s), index=s.index)
    return (s - s.min()) / rng


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def score_and_rank(
    alerts: list[Alert],
    recurrence_counts: dict[int, int] | None = None,
    weights: dict | None = None,
) -> pd.DataFrame:
    """
    Puntúa y ordena las alertas por prioridad.

    Args:
        alerts: Lista de alertas (salida de rules.run_all_rules).
        recurrence_counts: Mapeo {idproducto: n_cierres_con_faltante} para
                           calcular el factor de recurrencia. Si es None, se ignora.
        weights: Pesos personalizados. Usa WEIGHTS por defecto.

    Returns:
        DataFrame con columnas:
            rank, rule_id, severity, category, product, categoria_nombre,
            value_mxn, pct_variance, diferencia, recurrences,
            severity_score, recurrence_factor, priority_score, message
    """
    _EMPTY_COLS = [
        "rank", "rule_id", "severity", "category", "product", "categoria_nombre",
        "value_mxn", "pct_variance", "diferencia", "recurrences",
        "severity_score", "recurrence_factor", "priority_score", "message",
    ]
    if not alerts:
        return pd.DataFrame(columns=_EMPTY_COLS)

    w = weights or WEIGHTS
    df = alerts_to_dataframe(alerts).copy()

    # -- Garantizar tipos numéricos (pandas puede inferir object si hay None/nan) --
    for col in ("value_mxn", "pct_variance", "diferencia"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # -- Severidad numérica -------------------------------------------------
    df["severity_score"] = df["severity"].map(SEVERITY_SCORE).fillna(1)

    # -- Factor de recurrencia ----------------------------------------------
    if recurrence_counts:
        df["recurrences"] = df["idproducto"].map(recurrence_counts).fillna(0)
    else:
        df["recurrences"] = 0

    # Recurrence factor: 1.0 (sin historial) hasta MAX_RECURRENCE_FACTOR
    df["recurrence_factor"] = 1.0 + (
        df["recurrences"].clip(upper=MAX_RECURRENCE_FACTOR - 1) / (MAX_RECURRENCE_FACTOR - 1)
        * (MAX_RECURRENCE_FACTOR - 1)
    )
    # Simplify: factor lineal entre 1.0 y MAX_RECURRENCE_FACTOR
    df["recurrence_factor"] = (
        1.0
        + (df["recurrences"].clip(upper=10) / 10) * (MAX_RECURRENCE_FACTOR - 1.0)
    ).clip(upper=MAX_RECURRENCE_FACTOR)

    # -- Impacto monetario absoluto ----------------------------------------
    df["abs_value_mxn"] = df["value_mxn"].abs()

    # -- Normalizar cada componente ----------------------------------------
    norm_mxn      = _normalize_series(df["abs_value_mxn"])
    norm_severity = _normalize_series(df["severity_score"].astype(float))
    norm_recurr   = _normalize_series(df["recurrence_factor"])

    # -- Score compuesto ---------------------------------------------------
    df["priority_score"] = (
        w["w_mxn"]        * norm_mxn
        + w["w_severity"] * norm_severity
        + w["w_recurrence"] * norm_recurr
    )

    # -- Ordenar: CRITICA > ALTA > MEDIA > BAJA, luego por score desc ------
    severity_order = {"CRITICA": 0, "ALTA": 1, "MEDIA": 2, "BAJA": 3}
    df["_sev_order"] = df["severity"].map(severity_order).fillna(9)
    df = df.sort_values(
        ["_sev_order", "priority_score"],
        ascending=[True, False],
    ).reset_index(drop=True)

    df["rank"] = df.index + 1

    # -- Seleccionar y ordenar columnas de salida --------------------------
    output_cols = [
        "rank", "rule_id", "severity", "category",
        "product", "categoria_nombre",
        "value_mxn", "pct_variance", "diferencia",
        "recurrences", "severity_score", "recurrence_factor",
        "priority_score", "message",
    ]
    return df[[c for c in output_cols if c in df.columns]]


# ---------------------------------------------------------------------------
# Helpers para reportes
# ---------------------------------------------------------------------------

def summary_by_severity(df_ranked: pd.DataFrame) -> pd.DataFrame:
    """
    Resumen del número de alertas y el impacto total en MXN por nivel de severidad.
    """
    if df_ranked.empty:
        return pd.DataFrame()
    grp = (
        df_ranked.groupby("severity")
        .agg(
            n_alertas=("rule_id", "count"),
            impacto_total_mxn=("value_mxn", "sum"),
            impacto_abs_mxn=("value_mxn", lambda x: x.abs().sum()),
        )
        .reset_index()
    )
    order = {"CRITICA": 0, "ALTA": 1, "MEDIA": 2, "BAJA": 3}
    grp["_order"] = grp["severity"].map(order)
    return grp.sort_values("_order").drop(columns="_order").reset_index(drop=True)


def summary_by_category(df_ranked: pd.DataFrame) -> pd.DataFrame:
    """
    Resumen del número de alertas y el impacto en MXN por tipo de hallazgo.
    """
    if df_ranked.empty:
        return pd.DataFrame()
    return (
        df_ranked.groupby("category")
        .agg(
            n_alertas=("rule_id", "count"),
            impacto_total_mxn=("value_mxn", "sum"),
            impacto_abs_mxn=("value_mxn", lambda x: x.abs().sum()),
        )
        .sort_values("impacto_abs_mxn", ascending=False)
        .reset_index()
    )


def top_n_findings(df_ranked: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Retorna los N hallazgos más prioritarios."""
    return df_ranked.head(n)


def compute_recurrence_counts(
    df_history: pd.DataFrame,
    idproductos: list[int] | None = None,
) -> dict[int, int]:
    """
    Calcula cuántos cierres históricos recientes tuvieron faltante (diferencia < 0)
    para cada producto.

    Args:
        df_history: DataFrame con columnas 'idproducto' y 'diferencia'.
                    Típicamente concatenación de varias llamadas a
                    queries.get_product_variance_history().
        idproductos: Si se especifica, filtra solo esos productos.

    Returns:
        Dict {idproducto: n_cierres_con_faltante}
    """
    if df_history.empty:
        return {}
    df = df_history.copy()
    if idproductos:
        df = df[df["idproducto"].isin(idproductos)]
    faltantes = df[df["diferencia"] < 0]
    return faltantes.groupby("idproducto").size().to_dict()
