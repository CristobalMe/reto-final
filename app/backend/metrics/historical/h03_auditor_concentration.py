from __future__ import annotations

import math

from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import HistoricalContext, HistoricalMetric, MetricMeta
from ..registry import register_historical


class H03Thresholds(BaseModel):
    min_closures: int = 3
    z_high: float = 1.5
    self_closure_share_high: float = 0.5  # >50% of this auditor's closures are self-captured


@register_historical
class H03AuditorConcentration(HistoricalMetric):
    meta = MetricMeta(
        id="H03",
        name="Concentración de variance por auditor",
        description="Flags auditors whose closures in this branch show consistently higher shortages than peers, or who frequently close their own captures.",
        category="AUDITOR_OUTLIER",
        severity_hint=Severity.ALTA,
    )
    thresholds = H03Thresholds()

    def compute(self, ctx: HistoricalContext) -> list[Finding]:
        t = self.thresholds
        stats = ctx.auditor_stats
        if stats is None or stats.empty:
            return []

        eligible = stats[stats["closures_count"] >= t.min_closures].copy()
        if eligible.empty:
            return []

        avg_series = eligible["avg_faltantes"].astype(float)
        mean = float(avg_series.mean())
        std = float(avg_series.std(ddof=1)) if len(eligible) > 1 else 0.0

        out: list[Finding] = []
        for _, row in eligible.iterrows():
            idauditor = int(row["idauditor"])
            avg_fal = float(row["avg_faltantes"])
            closures = int(row["closures_count"])
            self_closures = int(row.get("self_closures") or 0)
            self_share = self_closures / closures if closures else 0.0

            reasons: list[str] = []
            severity = Severity.MEDIA

            if std > 0 and not math.isnan(std):
                z = (avg_fal - mean) / std
                if abs(z) >= t.z_high:
                    reasons.append(f"faltante promedio z={z:.2f} vs pares")
                    severity = Severity.ALTA

            if self_share >= t.self_closure_share_high:
                reasons.append(f"{self_share*100:.0f}% de cierres auto-capturados")
                severity = Severity.CRITICA  # SoD concentration is serious

            if not reasons:
                continue

            out.append(Finding(
                metric_id=self.meta.id,
                severity=severity,
                category=self.meta.category,
                message=(
                    f"Auditor {idauditor}: " + "; ".join(reasons) +
                    f" (en {closures} cierres)."
                ),
                idauditor=idauditor,
                idsucursal=ctx.idsucursal,
                value_mxn=avg_fal,
                extra={
                    "closures_count": closures,
                    "avg_faltantes": avg_fal,
                    "self_closure_share": self_share,
                    "peer_mean_avg_faltantes": mean,
                },
            ))
        return out
