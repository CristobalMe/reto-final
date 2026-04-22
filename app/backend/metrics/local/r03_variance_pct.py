from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import LocalMetric, MetricMeta
from ..registry import register_local
from ._helpers import make_finding


class R03Thresholds(BaseModel):
    pct_high: float = 15.0
    pct_critical: float = 30.0
    min_stockteorico: float = 1.0
    min_abs_diferencia: float = 0.5


@register_local
class R03VariancePct(LocalMetric):
    meta = MetricMeta(
        id="R03",
        name="Variación % elevada vs stock teórico",
        description="Percent difference between physical and theoretical stock exceeds threshold.",
        category="VARIANCE",
        severity_hint=Severity.ALTA,
    )
    thresholds = R03Thresholds()

    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]:
        t = self.thresholds
        out: list[Finding] = []
        for _, row in df.iterrows():
            stockteorico = float(row.get("stockteorico") or 0)
            diferencia = float(row.get("diferencia") or 0)
            if stockteorico < t.min_stockteorico or abs(diferencia) < t.min_abs_diferencia:
                continue
            pct = (diferencia / stockteorico) * 100
            if abs(pct) > 10_000:  # corrupt
                continue
            if abs(pct) >= t.pct_critical:
                out.append(make_finding(
                    self.meta.id, Severity.CRITICA, self.meta.category, row,
                    f"Variación {pct:.1f}% vs stock teórico.",
                    pct_variance=pct,
                ))
            elif abs(pct) >= t.pct_high:
                out.append(make_finding(
                    self.meta.id, Severity.ALTA, self.meta.category, row,
                    f"Variación {pct:.1f}% vs stock teórico.",
                    pct_variance=pct,
                ))
        return out
