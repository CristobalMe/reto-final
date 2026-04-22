from __future__ import annotations

from typing import TypeVar

import pandas as pd

from domain.models import Finding, MetricCatalogEntry, MetricScope

from .base import BaseMetric, HistoricalContext, HistoricalMetric, LocalMetric

_LOCAL: dict[str, LocalMetric] = {}
_HISTORICAL: dict[str, HistoricalMetric] = {}

L = TypeVar("L", bound=type[LocalMetric])
H = TypeVar("H", bound=type[HistoricalMetric])


def register_local(cls: L) -> L:
    instance = cls()
    if instance.meta.id in _LOCAL:
        raise ValueError(f"Duplicate local metric id: {instance.meta.id}")
    _LOCAL[instance.meta.id] = instance
    return cls


def register_historical(cls: H) -> H:
    instance = cls()
    if instance.meta.id in _HISTORICAL:
        raise ValueError(f"Duplicate historical metric id: {instance.meta.id}")
    _HISTORICAL[instance.meta.id] = instance
    return cls


def all_local() -> list[LocalMetric]:
    return list(_LOCAL.values())


def all_historical() -> list[HistoricalMetric]:
    return list(_HISTORICAL.values())


def catalog() -> list[MetricCatalogEntry]:
    entries: list[MetricCatalogEntry] = []
    for m in _LOCAL.values():
        entries.append(_entry(m, MetricScope.LOCAL))
    for m in _HISTORICAL.values():
        entries.append(_entry(m, MetricScope.HISTORICAL))
    entries.sort(key=lambda e: e.id)
    return entries


def _entry(m: BaseMetric, scope: MetricScope) -> MetricCatalogEntry:
    return MetricCatalogEntry(
        id=m.meta.id,
        name=m.meta.name,
        description=m.meta.description,
        scope=scope,
        category=m.meta.category,
        severity_hint=m.meta.severity_hint,
    )


def run_all_local(df: pd.DataFrame, header: dict) -> list[Finding]:
    findings: list[Finding] = []
    for metric in _LOCAL.values():
        try:
            findings.extend(metric.compute(df, header))
        except Exception as exc:
            findings.append(
                Finding(
                    metric_id=metric.meta.id,
                    severity=metric.meta.severity_hint,
                    category="ERROR",
                    message=f"Metric {metric.meta.id} failed: {exc}",
                )
            )
    return findings


def run_all_historical(ctx: HistoricalContext) -> list[Finding]:
    findings: list[Finding] = []
    for metric in _HISTORICAL.values():
        try:
            findings.extend(metric.compute(ctx))
        except Exception as exc:
            findings.append(
                Finding(
                    metric_id=metric.meta.id,
                    severity=metric.meta.severity_hint,
                    category="ERROR",
                    message=f"Metric {metric.meta.id} failed: {exc}",
                )
            )
    return findings
