from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import LocalMetric, MetricMeta
from ..registry import register_local
from ._helpers import make_finding


class R04Thresholds(BaseModel):
    min_stock_drop_units: float = 1.0
    max_sales_tolerance: float = 0.0  # sales must be essentially zero


@register_local
class R04StockDropNoSales(LocalMetric):
    meta = MetricMeta(
        id="R04",
        name="Caída de stock sin ventas registradas",
        description="Theoretical stock decreases meaningfully but zero sales were recorded — suggests unregistered consumption.",
        category="UNREGISTERED_CONSUMPTION",
        severity_hint=Severity.MEDIA,
    )
    thresholds = R04Thresholds()

    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]:
        t = self.thresholds
        out: list[Finding] = []
        for _, row in df.iterrows():
            stockinicial = float(row.get("stockinicial") or 0)
            stockteorico = float(row.get("stockteorico") or 0)
            egresoventa = float(row.get("egresoventa") or 0)
            diferencia = float(row.get("diferencia") or 0)
            drop = stockinicial - stockteorico
            if drop >= t.min_stock_drop_units and egresoventa <= t.max_sales_tolerance and diferencia < 0:
                out.append(make_finding(
                    self.meta.id, Severity.MEDIA, self.meta.category, row,
                    f"Stock bajó {drop:.2f} unidades pero no se registraron ventas.",
                ))
        return out
