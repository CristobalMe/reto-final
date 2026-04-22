from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import LocalMetric, MetricMeta
from ..registry import register_local
from ._helpers import make_finding


class R09Thresholds(BaseModel):
    # Flag when stockfisico is an exact multiple of these values and stockteorico is not
    round_multiples: tuple[float, ...] = (100.0, 50.0, 10.0)
    min_stockfisico: float = 10.0
    min_theoretical_gap: float = 2.0  # how far stockteorico must differ from a round value


@register_local
class R09RoundNumberCount(LocalMetric):
    meta = MetricMeta(
        id="R09",
        name="Conteo físico sospechosamente redondo",
        description="Physical count is an exact round number (100, 50, 10) while theoretical stock is clearly not — possible fabricated count.",
        category="FABRICATED_COUNT",
        severity_hint=Severity.MEDIA,
    )
    thresholds = R09Thresholds()

    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]:
        t = self.thresholds
        out: list[Finding] = []
        for _, row in df.iterrows():
            stockfisico = float(row.get("stockfisico") or 0)
            stockteorico = float(row.get("stockteorico") or 0)
            if stockfisico < t.min_stockfisico:
                continue
            # Is stockfisico an exact multiple of any configured round value?
            hit = None
            for m in t.round_multiples:
                if m > 0 and stockfisico % m == 0:
                    hit = m
                    break
            if hit is None:
                continue
            # And the theoretical was not already round-ish
            if abs(stockteorico - stockfisico) < t.min_theoretical_gap:
                continue
            out.append(make_finding(
                self.meta.id, Severity.MEDIA, self.meta.category, row,
                f"Conteo físico redondo ({stockfisico:.0f}) vs teórico {stockteorico:.2f}.",
            ))
        return out
