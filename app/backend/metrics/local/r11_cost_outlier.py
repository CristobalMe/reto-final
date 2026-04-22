from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import LocalMetric, MetricMeta
from ..registry import register_local
from ._helpers import make_finding


class R11Thresholds(BaseModel):
    deviation_pct: float = 40.0  # |costopromedio - producto_costo_ref| / ref * 100
    min_reference_cost: float = 1.0


@register_local
class R11CostOutlier(LocalMetric):
    meta = MetricMeta(
        id="R11",
        name="Costo promedio anómalo vs catálogo",
        description="Average cost on the line item deviates from the product's reference cost by more than X%. May indicate mis-pricing or mis-posted receipts.",
        category="COST_ANOMALY",
        severity_hint=Severity.MEDIA,
    )
    thresholds = R11Thresholds()

    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]:
        t = self.thresholds
        out: list[Finding] = []
        for _, row in df.iterrows():
            costo = float(row.get("costopromedio") or 0)
            ref = float(row.get("producto_costo_ref") or 0)
            if ref < t.min_reference_cost or costo <= 0:
                continue
            dev = abs(costo - ref) / ref * 100
            if dev >= t.deviation_pct:
                out.append(make_finding(
                    self.meta.id, Severity.MEDIA, self.meta.category, row,
                    f"Costo promedio ${costo:.2f} vs catálogo ${ref:.2f} ({dev:.1f}% de desviación).",
                    pct_variance=dev,
                ))
        return out
