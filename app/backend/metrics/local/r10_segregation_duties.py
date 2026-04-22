from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from domain.models import Finding, Severity

from ..base import LocalMetric, MetricMeta
from ..registry import register_local


class R10Thresholds(BaseModel):
    # No numeric thresholds; rule is identity-based.
    pass


@register_local
class R10SegregationOfDuties(LocalMetric):
    meta = MetricMeta(
        id="R10",
        name="Sin segregación de funciones",
        description="The auditor of the closure is the same user that captured it (idauditor == idusuario). Classic fraud control violation.",
        category="SOD_VIOLATION",
        severity_hint=Severity.CRITICA,
    )
    thresholds = R10Thresholds()

    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]:
        idauditor = header.get("idauditor")
        idusuario = header.get("idusuario")
        idinventariomes = header.get("idinventariomes")
        idsucursal = header.get("idsucursal")
        if idauditor is None or idusuario is None:
            return []
        if int(idauditor) != int(idusuario):
            return []
        return [
            Finding(
                metric_id=self.meta.id,
                severity=Severity.CRITICA,
                category=self.meta.category,
                message=(
                    f"El auditor (id={idauditor}) es la misma persona que capturó el cierre. "
                    "Violación de segregación de funciones."
                ),
                idauditor=int(idauditor),
                idinventariomes=int(idinventariomes) if idinventariomes is not None else None,
                idsucursal=int(idsucursal) if idsucursal is not None else None,
                value_mxn=float(header.get("faltantes") or 0),
            )
        ]
