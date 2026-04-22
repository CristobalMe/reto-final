from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import LocalMetric, MetricMeta
from ..registry import register_local
from ._helpers import make_finding


class R05Thresholds(BaseModel):
    min_purchase_units: float = 2.0
    consumption_pct_cutoff: float = 5.0  # if consumption < 5% of purchase → flag


@register_local
class R05PurchaseNoConsumption(LocalMetric):
    meta = MetricMeta(
        id="R05",
        name="Compra sin consumo",
        description="Purchase recorded with negligible consumption — possible diversion or mis-entry.",
        category="UNUSED_PURCHASE",
        severity_hint=Severity.MEDIA,
    )
    thresholds = R05Thresholds()

    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]:
        t = self.thresholds
        out: list[Finding] = []
        for _, row in df.iterrows():
            compra = float(row.get("ingresocompra") or 0)
            venta = float(row.get("egresoventa") or 0)
            req = float(row.get("egresorequisicion") or 0)
            consumo = venta + req
            if compra < t.min_purchase_units:
                continue
            if consumo <= compra * (t.consumption_pct_cutoff / 100):
                pct = (consumo / compra * 100) if compra else 0
                out.append(make_finding(
                    self.meta.id, Severity.MEDIA, self.meta.category, row,
                    f"Compra de {compra:.2f} con consumo de solo {consumo:.2f} ({pct:.1f}%).",
                ))
        return out
