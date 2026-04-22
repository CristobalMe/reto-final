from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from domain.models import Finding, MetricScope, Severity


@dataclass(frozen=True)
class MetricMeta:
    id: str
    name: str
    description: str
    category: str
    severity_hint: Severity


class BaseMetric(ABC):
    meta: MetricMeta
    scope: MetricScope


class LocalMetric(BaseMetric, ABC):
    """Operates on a single closure's line-item DataFrame.

    The DataFrame carries one row per product in the closure, with stock,
    movement, variance and category columns (see repositories/closures.py).
    """

    scope = MetricScope.LOCAL

    @abstractmethod
    def compute(self, df: pd.DataFrame, header: dict) -> list[Finding]: ...


class HistoricalContext:
    """Bundle of cross-closure data passed to historical metrics.

    Kept as a plain class so new metrics can read additional slices without
    changing anybody else's signature.
    """

    def __init__(
        self,
        idsucursal: int,
        months_back: int,
        closures: pd.DataFrame,
        details: pd.DataFrame,
        auditor_stats: pd.DataFrame,
    ):
        self.idsucursal = idsucursal
        self.months_back = months_back
        self.closures = closures
        self.details = details
        self.auditor_stats = auditor_stats


class HistoricalMetric(BaseMetric, ABC):
    """Operates across many closures for a branch / product / auditor."""

    scope = MetricScope.HISTORICAL

    @abstractmethod
    def compute(self, ctx: HistoricalContext) -> list[Finding]: ...
