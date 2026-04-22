from __future__ import annotations

import math

from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import HistoricalContext, HistoricalMetric, MetricMeta
from ..registry import register_historical


class H02Thresholds(BaseModel):
    z_high: float = 2.0
    z_critical: float = 3.0
    min_samples: int = 6


@register_historical
class H02BranchZScore(HistoricalMetric):
    meta = MetricMeta(
        id="H02",
        name="Z-score de cierres de la sucursal",
        description="Flags closures whose total shortage is statistically anomalous against the branch's own history.",
        category="BRANCH_OUTLIER",
        severity_hint=Severity.ALTA,
    )
    thresholds = H02Thresholds()

    def compute(self, ctx: HistoricalContext) -> list[Finding]:
        t = self.thresholds
        closures = ctx.closures
        if closures is None or closures.empty or len(closures) < t.min_samples:
            return []
        values = closures["faltantes"].astype(float)
        mean = float(values.mean())
        std = float(values.std(ddof=1))
        if std == 0 or math.isnan(std):
            return []

        out: list[Finding] = []
        for _, row in closures.iterrows():
            val = float(row["faltantes"])
            z = (val - mean) / std
            if z <= -t.z_critical or z >= t.z_critical:
                sev = Severity.CRITICA
            elif z <= -t.z_high or z >= t.z_high:
                sev = Severity.ALTA
            else:
                continue
            out.append(Finding(
                metric_id=self.meta.id,
                severity=sev,
                category=self.meta.category,
                message=f"Cierre con z-score {z:.2f} (faltantes ${val:,.2f}, media sucursal ${mean:,.2f}).",
                idsucursal=ctx.idsucursal,
                idinventariomes=int(row["idinventariomes"]),
                idauditor=int(row["idauditor"]) if row.get("idauditor") is not None and not _isnan(row["idauditor"]) else None,
                value_mxn=val,
                extra={"z_score": z, "branch_mean_faltantes": mean, "branch_std_faltantes": std},
            ))
        return out


def _isnan(v) -> bool:
    try:
        return math.isnan(float(v))
    except (TypeError, ValueError):
        return False
