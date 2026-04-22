from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import LocalMetric, MetricMeta
from ..registry import register_local
from ._helpers import make_finding


class R08Thresholds(BaseModel):
    min_stockteorico: float = 5.0
    min_movement_abs: float = 0.1  # at least some movement to suspect missed count


@register_local
class R08NoPhysicalCount(LocalMetric):
    meta = MetricMeta(
        id="R08",
        name="Sin conteo físico",
        description="stockfisico is zero while theoretical stock and movement are non-trivial — likely missed count.",
        category="MISSING_COUNT",
        severity_hint=Severity.MEDIA,
    )
    thresholds = R08Thresholds()

    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]:
        t = self.thresholds
        out: list[Finding] = []
        for _, row in df.iterrows():
            stockfisico = float(row.get("stockfisico") or 0)
            stockteorico = float(row.get("stockteorico") or 0)
            movement = (
                float(row.get("ingresocompra") or 0)
                + float(row.get("egresoventa") or 0)
                + float(row.get("egresorequisicion") or 0)
                + float(row.get("ingresorequisicion") or 0)
            )
            if stockfisico == 0 and stockteorico >= t.min_stockteorico and abs(movement) >= t.min_movement_abs:
                out.append(make_finding(
                    self.meta.id, Severity.MEDIA, self.meta.category, row,
                    f"Sin conteo físico (stock teórico {stockteorico:.2f}, movimiento {movement:.2f}).",
                ))
        return out
