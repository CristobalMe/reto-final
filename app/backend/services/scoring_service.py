from __future__ import annotations

from collections import defaultdict

from domain.models import (
    CategorySummary,
    Finding,
    SEVERITY_WEIGHT,
    Severity,
    SeveritySummary,
)

W_MXN = 0.65
W_SEVERITY = 0.25
W_META = 0.10


def rank_findings(findings: list[Finding]) -> list[Finding]:
    """Assign each finding a priority score in [0, 1] and return sorted by score desc."""
    if not findings:
        return []

    max_mxn = max((abs(f.value_mxn) for f in findings), default=0.0) or 1.0
    max_sev = max(SEVERITY_WEIGHT.values())

    for f in findings:
        mxn_norm = abs(f.value_mxn) / max_mxn
        sev_raw = SEVERITY_WEIGHT.get(Severity(f.severity), 1)
        sev_norm = sev_raw / max_sev
        meta_norm = _meta_component(f)
        f.score = round(
            W_MXN * mxn_norm + W_SEVERITY * sev_norm + W_META * meta_norm, 4
        )

    return sorted(
        findings,
        key=lambda x: (SEVERITY_WEIGHT.get(Severity(x.severity), 0), x.score),
        reverse=True,
    )


def _meta_component(f: Finding) -> float:
    """Boost findings that report recurrence or high % variance."""
    rec = f.extra.get("consecutive_shortages") if isinstance(f.extra, dict) else None
    if rec:
        return min(float(rec) / 10.0, 1.0)
    share = f.extra.get("shortage_share") if isinstance(f.extra, dict) else None
    if share:
        return float(share)
    if f.pct_variance is not None:
        return min(abs(float(f.pct_variance)) / 100.0, 1.0)
    return 0.0


def summarize_by_severity(findings: list[Finding]) -> list[SeveritySummary]:
    acc: dict[str, list[float]] = defaultdict(list)
    for f in findings:
        acc[f.severity].append(f.value_mxn)
    out: list[SeveritySummary] = []
    order = [Severity.CRITICA.value, Severity.ALTA.value, Severity.MEDIA.value, Severity.BAJA.value]
    for sev in order:
        if sev in acc:
            out.append(SeveritySummary(
                severity=Severity(sev),
                count=len(acc[sev]),
                total_impact_mxn=round(sum(acc[sev]), 2),
            ))
    return out


def summarize_by_category(findings: list[Finding]) -> list[CategorySummary]:
    acc: dict[str, list[float]] = defaultdict(list)
    for f in findings:
        acc[f.category].append(f.value_mxn)
    out = [
        CategorySummary(category=k, count=len(v), total_impact_mxn=round(sum(v), 2))
        for k, v in acc.items()
    ]
    out.sort(key=lambda c: abs(c.total_impact_mxn), reverse=True)
    return out
