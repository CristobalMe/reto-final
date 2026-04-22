from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import LocalMetric, MetricMeta
from ..registry import register_local
from ._helpers import make_finding


class R06Thresholds(BaseModel):
    reajuste_pct: float = 10.0  # |reajuste| > this % of stock_teorico → flag
    min_stockteorico: float = 1.0


@register_local
class R06HighAdjustments(LocalMetric):
    meta = MetricMeta(
        id="R06",
        name="Reajuste manual elevado",
        description="Manual adjustment (reajuste) exceeds X% of theoretical stock. Possible audit-trail tampering.",
        category="MANUAL_ADJUSTMENT",
        severity_hint=Severity.ALTA,
    )
    thresholds = R06Thresholds()

    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]:
        t = self.thresholds
        out: list[Finding] = []
        for _, row in df.iterrows():
            reajuste = float(row.get("reajuste") or 0)
            stockteorico = float(row.get("stockteorico") or 0)
            if stockteorico < t.min_stockteorico or reajuste == 0:
                continue
            pct = abs(reajuste) / stockteorico * 100
            if pct >= t.reajuste_pct:
                sign = "+" if reajuste > 0 else ""
                out.append(make_finding(
                    self.meta.id, Severity.ALTA, self.meta.category, row,
                    f"Reajuste manual de {sign}{reajuste:.2f} unidades ({pct:.1f}% del stock teórico).",
                    pct_variance=pct,
                ))
        return out
