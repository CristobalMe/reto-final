from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    CRITICA = "CRITICA"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


SEVERITY_WEIGHT: dict[Severity, int] = {
    Severity.CRITICA: 4,
    Severity.ALTA: 3,
    Severity.MEDIA: 2,
    Severity.BAJA: 1,
}


class MetricScope(str, Enum):
    LOCAL = "LOCAL"
    HISTORICAL = "HISTORICAL"


class MetricCatalogEntry(BaseModel):
    id: str
    name: str
    description: str
    scope: MetricScope
    category: str
    severity_hint: Severity


class Finding(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    metric_id: str
    severity: Severity
    category: str
    message: str
    score: float = 0.0

    idproducto: int | None = None
    product_name: str | None = None
    categoria_nombre: str | None = None

    value_mxn: float = 0.0
    pct_variance: float | None = None
    diferencia: float | None = None

    idsucursal: int | None = None
    idauditor: int | None = None
    idinventariomes: int | None = None

    extra: dict = Field(default_factory=dict)


class ClosureHeader(BaseModel):
    idinventariomes: int
    idsucursal: int
    idalmacen: int
    idauditor: int | None
    idusuario: int
    fecha: datetime | None
    estatus: str
    total: float
    faltantes: float
    sobrantes: float
    total_fisico: float


class SeveritySummary(BaseModel):
    severity: Severity
    count: int
    total_impact_mxn: float


class CategorySummary(BaseModel):
    category: str
    count: int
    total_impact_mxn: float


class LocalReport(BaseModel):
    idinventariomes: int
    header: ClosureHeader | None
    findings: list[Finding]
    summary_by_severity: list[SeveritySummary]
    summary_by_category: list[CategorySummary]


class HistoricalReport(BaseModel):
    idsucursal: int
    months_back: int
    closures_analyzed: int
    findings: list[Finding]
    summary_by_severity: list[SeveritySummary]
    summary_by_category: list[CategorySummary]
