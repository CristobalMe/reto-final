from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import LocalMetric, MetricMeta
from ..registry import register_local
from ._helpers import make_finding


class R07Thresholds(BaseModel):
    devolucion_pct: float = 5.0
    min_stockteorico: float = 1.0


@register_local
class R07WasteExcess(LocalMetric):
    meta = MetricMeta(
        id="R07",
        name="Devolución / merma excesiva",
        description="Returns or waste exceed X% of theoretical stock — may conceal shrinkage.",
        category="WASTE",
        severity_hint=Severity.ALTA,
    )
    thresholds = R07Thresholds()

    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]:
        t = self.thresholds
        out: list[Finding] = []
        for _, row in df.iterrows():
            devol = float(row.get("egresodevolucion") or 0)
            stockteorico = float(row.get("stockteorico") or 0)
            if stockteorico < t.min_stockteorico or devol <= 0:
                continue
            pct = devol / stockteorico * 100
            if pct >= t.devolucion_pct:
                out.append(make_finding(
                    self.meta.id, Severity.ALTA, self.meta.category, row,
                    f"Devolución/merma de {devol:.2f} ({pct:.1f}% del stock teórico).",
                    pct_variance=pct,
                ))
        return out
