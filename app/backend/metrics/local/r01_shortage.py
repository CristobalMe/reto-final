from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import LocalMetric, MetricMeta
from ..registry import register_local
from ._helpers import cat_value, make_finding


class R01Thresholds(BaseModel):
    critical_mxn: dict[str, float] = {
        "Bebidas": -2_000,
        "Alimentos": -3_000,
        "Gastos": -5_000,
        "_default": -3_000,
    }
    high_mxn: dict[str, float] = {
        "Bebidas": -500,
        "Alimentos": -800,
        "Gastos": -1_500,
        "_default": -800,
    }
    unit_fallback_min_units: float = 2.0


@register_local
class R01Shortage(LocalMetric):
    meta = MetricMeta(
        id="R01",
        name="Faltante significativo",
        description="Flags products whose monetary shortage exceeds category-specific MXN cutoffs.",
        category="SHORTAGE",
        severity_hint=Severity.ALTA,
    )
    thresholds = R01Thresholds()

    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]:
        t = self.thresholds
        out: list[Finding] = []
        for _, row in df.iterrows():
            difimporte = float(row.get("difimporte") or 0)
            diferencia = float(row.get("diferencia") or 0)
            costo = float(row.get("costopromedio") or 0)
            cat = row.get("categoria_nombre")

            # Unit fallback when cost is zero (still a real shortage)
            if costo == 0 and difimporte == 0:
                if diferencia <= -t.unit_fallback_min_units:
                    out.append(
                        make_finding(
                            self.meta.id, Severity.MEDIA, self.meta.category, row,
                            f"Faltante de {abs(diferencia):.2f} unidades (sin costo cargado).",
                        )
                    )
                continue

            crit = cat_value(t.critical_mxn, cat)
            high = cat_value(t.high_mxn, cat)
            if difimporte <= crit:
                out.append(
                    make_finding(
                        self.meta.id, Severity.CRITICA, self.meta.category, row,
                        f"Faltante crítico: ${difimporte:,.2f} MXN.",
                    )
                )
            elif difimporte <= high:
                out.append(
                    make_finding(
                        self.meta.id, Severity.ALTA, self.meta.category, row,
                        f"Faltante elevado: ${difimporte:,.2f} MXN.",
                    )
                )
        return out
