"""
rules.py — Motor de reglas de alerta para el Cierre de Semana (TALOS).

Cada regla recibe un DataFrame de detalle (salida de queries.get_cierre_semana)
y devuelve una lista de dicts con estructura uniforme de alerta.

Uso:
    from src.rules import run_all_rules, DEFAULT_THRESHOLDS

    alerts = run_all_rules(df_detalle, thresholds=DEFAULT_THRESHOLDS,
                           df_history=df_hist)  # df_history opcional para R07
"""

from __future__ import annotations

import pandas as pd
from typing import TypedDict


# ---------------------------------------------------------------------------
# Estructura de una alerta
# ---------------------------------------------------------------------------

class Alert(TypedDict):
    rule_id: str          # e.g. "R01"
    severity: str         # "CRITICA" | "ALTA" | "MEDIA" | "BAJA"
    category: str         # tipo de hallazgo
    product: str          # nombre del producto
    idproducto: int
    categoria_nombre: str
    value_mxn: float      # impacto monetario (negativo = faltante)
    pct_variance: float   # % variación vs teórico (NaN si stock_teorico = 0)
    diferencia: float     # diferencia en unidades
    message: str          # descripción legible en español


# ---------------------------------------------------------------------------
# Umbrales por defecto
# ---------------------------------------------------------------------------

# Umbrales absolutos en MXN para faltantes/sobrantes por categoría raíz.
# Ajusta con get_thresholds_by_category() para calibrar por datos reales.
DEFAULT_THRESHOLDS: dict = {
    # (faltante_critico, faltante_alto, sobrante_alto) en MXN negativos/positivos
    "Bebidas":   {"faltante_critico": -2_000, "faltante_alto": -500,  "sobrante_alto": 500},
    "Alimentos": {"faltante_critico": -3_000, "faltante_alto": -800,  "sobrante_alto": 800},
    "Gastos":    {"faltante_critico": -5_000, "faltante_alto": -1_500, "sobrante_alto": 1_500},
    "_default":  {"faltante_critico": -3_000, "faltante_alto": -800,  "sobrante_alto": 800},
    # % variación absoluta para R03
    "pct_variacion_alta": 15.0,    # >15% de diferencia vs teórico
    # Reajuste manual elevado (unidades) para R06
    "reajuste_umbral_pct": 10.0,   # reajuste > 10% del stock teórico
    # Merma/devolución excesiva para R08
    "merma_pct": 5.0,              # devolución > 5% del stock teórico
    # Compra sin consumo: si ingresocompra > 0 y egresoventa < X% de ingresocompra
    "compra_sin_consumo_pct": 5.0,
    # Sin conteo físico: stockfisico = 0 cuando stockteorico > umbral
    "sin_conteo_min_stockteorico": 1.0,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_cat_threshold(thresholds: dict, categoria: str, key: str) -> float:
    cat_map = thresholds.get(categoria, thresholds.get("_default", {}))
    return cat_map.get(key, thresholds["_default"][key])


def _pct_variance(row: pd.Series) -> float:
    if pd.isna(row["stockteorico"]) or row["stockteorico"] == 0:
        return float("nan")
    return (row["diferencia"] / row["stockteorico"]) * 100


def _alert(
    rule_id: str,
    severity: str,
    category: str,
    row: pd.Series,
    message: str,
    pct: float | None = None,
) -> Alert:
    return Alert(
        rule_id=rule_id,
        severity=severity,
        category=category,
        product=row.get("producto_nombre", ""),
        idproducto=int(row.get("idproducto", 0)),
        categoria_nombre=row.get("categoria_nombre", ""),
        value_mxn=float(row.get("difimporte", 0) or 0),
        pct_variance=pct if pct is not None else _pct_variance(row),
        diferencia=float(row.get("diferencia", 0) or 0),
        message=message,
    )


# ---------------------------------------------------------------------------
# Reglas individuales
# ---------------------------------------------------------------------------

def rule_R01_faltante_significativo(
    df: pd.DataFrame, thresholds: dict
) -> list[Alert]:
    """R01 — Faltante monetario significativo (difimporte muy negativo)."""
    alerts = []
    for _, row in df.iterrows():
        val = float(row.get("difimporte", 0) or 0)
        if val >= 0:
            continue
        cat = row.get("categoria_nombre", "_default")
        critico = _get_cat_threshold(thresholds, cat, "faltante_critico")
        alto = _get_cat_threshold(thresholds, cat, "faltante_alto")
        if val <= critico:
            sev = "CRITICA"
            msg = (
                f"Faltante crítico de ${abs(val):,.2f} MXN en '{row['producto_nombre']}' "
                f"(categoría: {cat}). Requiere revisión inmediata."
            )
        elif val <= alto:
            sev = "ALTA"
            msg = (
                f"Faltante significativo de ${abs(val):,.2f} MXN en '{row['producto_nombre']}' "
                f"(categoría: {cat})."
            )
        else:
            continue
        alerts.append(_alert("R01", sev, "Faltante", row, msg))
    return alerts


def rule_R02_sobrante_significativo(
    df: pd.DataFrame, thresholds: dict
) -> list[Alert]:
    """R02 — Sobrante monetario significativo (difimporte positivo inusual)."""
    alerts = []
    for _, row in df.iterrows():
        val = float(row.get("difimporte", 0) or 0)
        if val <= 0:
            continue
        cat = row.get("categoria_nombre", "_default")
        umbral = _get_cat_threshold(thresholds, cat, "sobrante_alto")
        if val >= umbral:
            msg = (
                f"Sobrante de ${val:,.2f} MXN en '{row['producto_nombre']}' "
                f"(categoría: {cat}). Verificar conteo o captura."
            )
            alerts.append(_alert("R02", "ALTA", "Sobrante", row, msg))
    return alerts


def rule_R03_variacion_pct_alta(
    df: pd.DataFrame, thresholds: dict
) -> list[Alert]:
    """R03 — Variación porcentual > umbral vs stock teórico."""
    umbral = thresholds.get("pct_variacion_alta", 15.0)
    alerts = []
    for _, row in df.iterrows():
        pct = _pct_variance(row)
        if pd.isna(pct):
            continue
        if abs(pct) > umbral:
            direction = "negativa" if pct < 0 else "positiva"
            msg = (
                f"Variación {direction} de {pct:.1f}% en '{row['producto_nombre']}' "
                f"({row.get('diferencia', 0):+.2f} {row.get('unidadmedida_nombre', 'u')} "
                f"vs teórico {row.get('stockteorico', 0):.2f})."
            )
            alerts.append(_alert("R03", "ALTA", "Variación %", row, msg, pct=pct))
    return alerts


def rule_R04_sin_ventas_con_movimiento(
    df: pd.DataFrame, thresholds: dict
) -> list[Alert]:
    """
    R04 — El stock teórico bajó (hay movimientos) pero egresoventa = 0.
    Puede indicar consumo no registrado en ventas o desvío.
    """
    alerts = []
    for _, row in df.iterrows():
        egresoventa = float(row.get("egresoventa", 0) or 0)
        stockinicial = float(row.get("stockinicial", 0) or 0)
        stockteorico = float(row.get("stockteorico", 0) or 0)
        diferencia = float(row.get("diferencia", 0) or 0)
        if egresoventa > 0:
            continue
        # Stock bajó sin ventas registradas
        consumo_sin_venta = stockinicial - stockteorico
        if consumo_sin_venta > 0 and diferencia < 0:
            msg = (
                f"'{row['producto_nombre']}' muestra consumo de {consumo_sin_venta:.2f} u "
                f"sin ventas registradas. Posible desvío o consumo no capturado."
            )
            alerts.append(_alert("R04", "MEDIA", "Ventas", row, msg))
    return alerts


def rule_R05_compra_sin_consumo(
    df: pd.DataFrame, thresholds: dict
) -> list[Alert]:
    """
    R05 — Ingreso por compra registrado pero egresoventa prácticamente nulo.
    Indica posible mercancía recibida que no se vendió/usó (o captura incorrecta).
    """
    umbral_pct = thresholds.get("compra_sin_consumo_pct", 5.0)
    alerts = []
    for _, row in df.iterrows():
        compra = float(row.get("ingresocompra", 0) or 0)
        venta = float(row.get("egresoventa", 0) or 0)
        if compra <= 0:
            continue
        pct_consumido = (venta / compra * 100) if compra > 0 else 0
        if pct_consumido < umbral_pct:
            msg = (
                f"'{row['producto_nombre']}' tiene compra de {compra:.2f} u "
                f"pero consumo en ventas de solo {venta:.2f} u "
                f"({pct_consumido:.1f}%). Verificar destino del inventario."
            )
            alerts.append(_alert("R05", "MEDIA", "Compras", row, msg))
    return alerts


def rule_R06_reajuste_manual_elevado(
    df: pd.DataFrame, thresholds: dict
) -> list[Alert]:
    """
    R06 — Reajuste manual > X% del stock teórico.
    Los reajustes son correcciones administrativas que deberían ser excepcionales.
    """
    umbral_pct = thresholds.get("reajuste_umbral_pct", 10.0)
    alerts = []
    for _, row in df.iterrows():
        reajuste = float(row.get("reajuste", 0) or 0)
        stockteorico = float(row.get("stockteorico", 0) or 0)
        if reajuste == 0:
            continue
        if stockteorico != 0:
            pct = abs(reajuste / stockteorico) * 100
        else:
            pct = float("nan")
        if abs(reajuste) > 0 and (pd.isna(pct) or pct >= umbral_pct):
            direction = "positivo" if reajuste > 0 else "negativo"
            msg = (
                f"Reajuste manual {direction} de {reajuste:+.2f} u en "
                f"'{row['producto_nombre']}'"
                + (f" ({pct:.1f}% del stock teórico)." if not pd.isna(pct) else ".")
            )
            alerts.append(_alert("R06", "ALTA", "Ajuste", row, msg))
    return alerts


def rule_R07_faltante_recurrente(
    df: pd.DataFrame,
    thresholds: dict,
    df_history: pd.DataFrame | None = None,
    consecutivos_min: int = 3,
) -> list[Alert]:
    """
    R07 — El mismo producto tiene faltante en >= N cierres consecutivos previos.
    Requiere df_history (salida de get_product_variance_history por producto).

    Si no se pasa df_history, se omite esta regla.
    """
    if df_history is None or df_history.empty:
        return []

    alerts = []
    # df_history debe tener columnas: idproducto, fecha, diferencia
    # Verificar recurrencia por producto
    recurrentes = set()
    for idprod, grp in df_history.groupby("idproducto") if "idproducto" in df_history.columns else []:
        grp_sorted = grp.sort_values("fecha", ascending=False)
        # Contar cuántos de los últimos cierres tienen diferencia < 0
        ultimos = grp_sorted.head(consecutivos_min)
        if len(ultimos) >= consecutivos_min and (ultimos["diferencia"] < 0).all():
            recurrentes.add(idprod)

    for _, row in df.iterrows():
        idprod = row.get("idproducto")
        if idprod in recurrentes:
            msg = (
                f"'{row['producto_nombre']}' presenta faltante en los últimos "
                f"{consecutivos_min} cierres consecutivos. Patrón recurrente crítico."
            )
            alerts.append(_alert("R07", "CRITICA", "Recurrencia", row, msg))
    return alerts


def rule_R08_merma_excesiva(
    df: pd.DataFrame, thresholds: dict
) -> list[Alert]:
    """
    R08 — Devolución/merma supera X% del stock teórico.
    Alta merma puede indicar mal manejo, caducidad o fraude en devoluciones.
    """
    umbral_pct = thresholds.get("merma_pct", 5.0)
    alerts = []
    for _, row in df.iterrows():
        merma = float(row.get("egresodevolucion", 0) or 0)
        stockteorico = float(row.get("stockteorico", 0) or 0)
        if merma <= 0 or stockteorico <= 0:
            continue
        pct = (merma / stockteorico) * 100
        if pct > umbral_pct:
            msg = (
                f"Merma/devolución de {merma:.2f} u en '{row['producto_nombre']}' "
                f"representa el {pct:.1f}% del stock teórico ({stockteorico:.2f} u). "
                f"Supera el umbral del {umbral_pct:.0f}%."
            )
            alerts.append(_alert("R08", "ALTA", "Merma", row, msg))
    return alerts


def rule_R09_bebida_alto_valor_con_faltante(
    df: pd.DataFrame, thresholds: dict
) -> list[Alert]:
    """
    R09 — Productos de Bebidas con faltante monetario (difimporte negativo).
    Las bebidas tienen alto margen y son objetivo frecuente de robo/desvío.
    Se aplica un umbral más sensible que R01 para esta categoría.
    """
    umbral = thresholds.get("Bebidas", {}).get("faltante_alto", -500)
    alerts = []
    for _, row in df.iterrows():
        cat = row.get("categoria_nombre", "")
        if "Beb" not in str(cat) and "beb" not in str(cat):
            continue
        val = float(row.get("difimporte", 0) or 0)
        if val < umbral:
            msg = (
                f"Faltante en bebida '{row['producto_nombre']}': ${abs(val):,.2f} MXN. "
                f"Las bebidas son categoría de alto riesgo."
            )
            alerts.append(_alert("R09", "CRITICA", "Bebidas", row, msg))
    return alerts


def rule_R10_sin_conteo_fisico(
    df: pd.DataFrame, thresholds: dict
) -> list[Alert]:
    """
    R10 — Producto con stock teórico positivo pero conteo físico = 0.
    Puede indicar que no se realizó el conteo o que el producto desapareció.
    """
    min_stock = thresholds.get("sin_conteo_min_stockteorico", 1.0)
    alerts = []
    for _, row in df.iterrows():
        stockfisico = float(row.get("stockfisico", 0) or 0)
        stockteorico = float(row.get("stockteorico", 0) or 0)
        if stockfisico != 0:
            continue
        if stockteorico >= min_stock:
            msg = (
                f"'{row['producto_nombre']}' tiene stock teórico de {stockteorico:.2f} u "
                f"pero conteo físico registrado como 0. Verificar si se realizó el conteo."
            )
            alerts.append(_alert("R10", "MEDIA", "Conteo", row, msg))
    return alerts


# ---------------------------------------------------------------------------
# Punto de entrada principal
# ---------------------------------------------------------------------------

ALL_RULES = [
    rule_R01_faltante_significativo,
    rule_R02_sobrante_significativo,
    rule_R03_variacion_pct_alta,
    rule_R04_sin_ventas_con_movimiento,
    rule_R05_compra_sin_consumo,
    rule_R06_reajuste_manual_elevado,
    rule_R08_merma_excesiva,
    rule_R09_bebida_alto_valor_con_faltante,
    rule_R10_sin_conteo_fisico,
]


def run_all_rules(
    df_detalle: pd.DataFrame,
    thresholds: dict | None = None,
    df_history: pd.DataFrame | None = None,
) -> list[Alert]:
    """
    Ejecuta todas las reglas sobre el DataFrame de detalle de un Cierre de Semana.

    Args:
        df_detalle: Salida de queries.get_cierre_semana()
        thresholds: Diccionario de umbrales. Usa DEFAULT_THRESHOLDS si es None.
        df_history: Historial de variaciones por producto para la regla R07.
                    Salida de queries.get_product_variance_history() con columna
                    'idproducto'. Puede ser None para omitir R07.

    Returns:
        Lista de alertas (dicts con estructura Alert).
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    alerts: list[Alert] = []

    for rule_fn in ALL_RULES:
        try:
            result = rule_fn(df_detalle, thresholds)
            alerts.extend(result)
        except Exception as exc:
            print(f"[WARN] Regla {rule_fn.__name__} falló: {exc}")

    # R07 requiere historial externo
    try:
        alerts.extend(rule_R07_faltante_recurrente(df_detalle, thresholds, df_history))
    except Exception as exc:
        print(f"[WARN] Regla R07 falló: {exc}")

    return alerts


def alerts_to_dataframe(alerts: list[Alert]) -> pd.DataFrame:
    """Convierte la lista de alertas a DataFrame para análisis y visualización."""
    if not alerts:
        return pd.DataFrame(columns=[
            "rule_id", "severity", "category", "product", "idproducto",
            "categoria_nombre", "value_mxn", "pct_variance", "diferencia", "message"
        ])
    return pd.DataFrame(alerts)
