from __future__ import annotations

from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import HistoricalContext, HistoricalMetric, MetricMeta
from ..registry import register_historical


class H01Thresholds(BaseModel):
    min_consecutive_shortages: int = 3
    min_shortage_mxn: float = -100.0  # treat anything at or below this as a shortage event


@register_historical
class H01RecurringShortage(HistoricalMetric):
    meta = MetricMeta(
        id="H01",
        name="Faltante recurrente",
        description="Product has shown shortages in N or more consecutive closures at the same branch.",
        category="RECURRING_SHORTAGE",
        severity_hint=Severity.CRITICA,
    )
    thresholds = H01Thresholds()

    def compute(self, ctx: HistoricalContext) -> list[Finding]:
        t = self.thresholds
        if ctx.details.empty:
            return []
        df = ctx.details.copy()
        df = df.sort_values(["idproducto", "fecha"])
        df["is_shortage"] = df["difimporte"].astype(float) <= t.min_shortage_mxn

        out: list[Finding] = []
        for idproducto, group in df.groupby("idproducto", sort=False):
            # Count tail of consecutive shortages (most recent first)
            shortages = group["is_shortage"].tolist()[::-1]
            run = 0
            for flag in shortages:
                if flag:
                    run += 1
                else:
                    break
            if run >= t.min_consecutive_shortages:
                last = group.iloc[-1]
                total_impact = float(group.tail(run)["difimporte"].sum())
                out.append(Finding(
                    metric_id=self.meta.id,
                    severity=Severity.CRITICA,
                    category=self.meta.category,
                    message=(
                        f"{run} cierres consecutivos con faltante. "
                        f"Impacto acumulado: ${total_impact:,.2f} MXN."
                    ),
                    idproducto=int(idproducto),
                    product_name=str(last.get("producto_nombre", "")),
                    categoria_nombre=str(last.get("categoria_nombre", "") or ""),
                    value_mxn=total_impact,
                    idsucursal=ctx.idsucursal,
                    extra={"consecutive_shortages": run},
                ))
        return out
