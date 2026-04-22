from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import LocalMetric, MetricMeta
from ..registry import register_local
from ._helpers import cat_value, make_finding


class R02Thresholds(BaseModel):
    high_mxn: dict[str, float] = {
        "Bebidas": 500,
        "Alimentos": 800,
        "Gastos": 1_500,
        "_default": 800,
    }


@register_local
class R02Surplus(LocalMetric):
    meta = MetricMeta(
        id="R02",
        name="Sobrante significativo",
        description="Flags products whose monetary surplus exceeds category cutoffs. May indicate stuffing or mis-counted theoretical stock.",
        category="SURPLUS",
        severity_hint=Severity.ALTA,
    )
    thresholds = R02Thresholds()

    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]:
        t = self.thresholds
        out: list[Finding] = []
        for _, row in df.iterrows():
            difimporte = float(row.get("difimporte") or 0)
            if difimporte <= 0:
                continue
            high = cat_value(t.high_mxn, row.get("categoria_nombre"))
            if difimporte >= high:
                out.append(
                    make_finding(
                        self.meta.id, Severity.ALTA, self.meta.category, row,
                        f"Sobrante elevado: ${difimporte:,.2f} MXN.",
                    )
                )
        return out
