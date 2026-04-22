from __future__ import annotations

from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import HistoricalContext, HistoricalMetric, MetricMeta
from ..registry import register_historical


class H04Thresholds(BaseModel):
    min_closures_appearing: int = 4
    min_shortage_share: float = 0.75  # product was short in >=75% of its closures
    min_shortage_mxn: float = -100.0


@register_historical
class H04ProductBranchPersistence(HistoricalMetric):
    meta = MetricMeta(
        id="H04",
        name="Faltante persistente producto-sucursal",
        description="Same product shows shortage in the majority of its closures at this branch — chronic leakage point.",
        category="CHRONIC_LEAKAGE",
        severity_hint=Severity.ALTA,
    )
    thresholds = H04Thresholds()

    def compute(self, ctx: HistoricalContext) -> list[Finding]:
        t = self.thresholds
        if ctx.details is None or ctx.details.empty:
            return []
        df = ctx.details.copy()
        df["is_shortage"] = df["difimporte"].astype(float) <= t.min_shortage_mxn

        out: list[Finding] = []
        grouped = df.groupby("idproducto")
        for idproducto, group in grouped:
            n = len(group)
            if n < t.min_closures_appearing:
                continue
            share = float(group["is_shortage"].mean())
            if share < t.min_shortage_share:
                continue
            total_impact = float(group["difimporte"].sum())
            last = group.iloc[-1]
            out.append(Finding(
                metric_id=self.meta.id,
                severity=Severity.ALTA,
                category=self.meta.category,
                message=(
                    f"Faltante en {int(share*100)}% de {n} cierres analizados. "
                    f"Impacto acumulado: ${total_impact:,.2f} MXN."
                ),
                idproducto=int(idproducto),
                product_name=str(last.get("producto_nombre", "")),
                categoria_nombre=str(last.get("categoria_nombre", "") or ""),
                idsucursal=ctx.idsucursal,
                value_mxn=total_impact,
                extra={"closures_analyzed": n, "shortage_share": share},
            ))
        return out
