from __future__ import annotations

import pandas as pd

from domain.models import Finding, Severity


def row_base_kwargs(row: pd.Series) -> dict:
    """Extract identifying fields from a detail row for Finding construction."""
    return dict(
        idproducto=_int_or_none(row.get("idproducto")),
        product_name=_str_or_none(row.get("producto_nombre")),
        categoria_nombre=_str_or_none(row.get("categoria_nombre")),
        value_mxn=_float(row.get("difimporte")),
        diferencia=_float(row.get("diferencia")),
        pct_variance=_pct_variance(row),
    )


def make_finding(
    metric_id: str, severity: Severity, category: str, row: pd.Series, message: str,
    **overrides,
) -> Finding:
    kwargs = row_base_kwargs(row)
    kwargs.update(overrides)
    return Finding(
        metric_id=metric_id,
        severity=severity,
        category=category,
        message=message,
        **kwargs,
    )


def cat_value(thresholds: dict[str, float], categoria: str | None) -> float:
    if categoria is None:
        return thresholds["_default"]
    return thresholds.get(categoria, thresholds["_default"])


def _pct_variance(row: pd.Series) -> float | None:
    stockteorico = row.get("stockteorico")
    diferencia = row.get("diferencia")
    if stockteorico is None or pd.isna(stockteorico) or float(stockteorico) == 0:
        return None
    pct = (float(diferencia or 0) / float(stockteorico)) * 100
    # Cap extreme outliers from corrupt data
    if pct > 10_000 or pct < -10_000:
        return None
    return pct


def _float(v) -> float:
    if v is None or pd.isna(v):
        return 0.0
    return float(v)


def _int_or_none(v) -> int | None:
    if v is None or pd.isna(v):
        return None
    return int(v)


def _str_or_none(v) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return str(v)
