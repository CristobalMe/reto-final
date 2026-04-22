from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine

from domain.models import ClosureHeader, HistoricalReport, LocalReport, ProductContext
from metrics.base import HistoricalContext
from metrics.registry import run_all_historical, run_all_local
from repositories import auditors as auditors_repo
from repositories import closures as closures_repo

from .scoring_service import rank_findings, summarize_by_category, summarize_by_severity


def compute_local_report(engine: Engine, idinventariomes: int) -> LocalReport:
    header_df = closures_repo.get_closure_header(engine, idinventariomes)
    if header_df.empty:
        return LocalReport(
            idinventariomes=idinventariomes,
            header=None,
            findings=[],
            summary_by_severity=[],
            summary_by_category=[],
        )
    header_row = header_df.iloc[0].to_dict()
    header = ClosureHeader(
        idinventariomes=int(header_row["idinventariomes"]),
        idsucursal=int(header_row["idsucursal"]),
        idalmacen=int(header_row["idalmacen"]),
        idauditor=_opt_int(header_row.get("idauditor")),
        idusuario=int(header_row["idusuario"]),
        fecha=header_row.get("fecha"),
        estatus=str(header_row.get("estatus") or ""),
        total=float(header_row.get("total") or 0),
        faltantes=float(header_row.get("faltantes") or 0),
        sobrantes=float(header_row.get("sobrantes") or 0),
        total_fisico=float(header_row.get("total_fisico") or 0),
        almacen_nombre=_opt_str(header_row.get("almacen_nombre")),
        almacen_encargado=_opt_str(header_row.get("almacen_encargado")),
    )

    detail = closures_repo.get_closure_detail(engine, idinventariomes)
    findings = run_all_local(detail, header_row)
    for f in findings:
        f.idinventariomes = header.idinventariomes
        if f.idsucursal is None:
            f.idsucursal = header.idsucursal
        if f.idauditor is None:
            f.idauditor = header.idauditor

    ranked = rank_findings(findings)
    context = _build_product_context(detail, ranked)
    return LocalReport(
        idinventariomes=idinventariomes,
        header=header,
        findings=ranked,
        summary_by_severity=summarize_by_severity(ranked),
        summary_by_category=summarize_by_category(ranked),
        context_by_idproducto=context,
    )


def _build_product_context(detail: pd.DataFrame, findings) -> dict[str, ProductContext]:
    ids = {f.idproducto for f in findings if f.idproducto is not None}
    if not ids or detail.empty:
        return {}
    subset = detail[detail["idproducto"].isin(ids)]
    out: dict[str, ProductContext] = {}
    for _, row in subset.iterrows():
        idp = int(row["idproducto"])
        out[str(idp)] = ProductContext(
            idproducto=idp,
            producto_nombre=str(row.get("producto_nombre") or ""),
            producto_clase=_opt_str(row.get("producto_clase")),
            unidad=_opt_str(row.get("unidadmedida_nombre")),
            categoria_nombre=_opt_str(row.get("categoria_nombre")),
            subcategoria_nombre=_opt_str(row.get("subcategoria_nombre")),
            stockinicial=float(row.get("stockinicial") or 0),
            stockteorico=float(row.get("stockteorico") or 0),
            stockfisico=float(row.get("stockfisico") or 0),
            diferencia=float(row.get("diferencia") or 0),
            difimporte=float(row.get("difimporte") or 0),
            costopromedio=float(row.get("costopromedio") or 0),
            ingresocompra=float(row.get("ingresocompra") or 0),
            ingresoordentablajeria=float(row.get("ingresoordentablajeria") or 0),
            egresoventa=float(row.get("egresoventa") or 0),
            egresoordentablajeria=float(row.get("egresoordentablajeria") or 0),
            egresodevolucion=float(row.get("egresodevolucion") or 0),
            aclaracion=_opt_str(row.get("aclaracion")),
        )
    return out


def _opt_str(v) -> str | None:
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    s = str(v).strip()
    return s if s else None


def compute_historical_report(
    engine: Engine, idsucursal: int, months: int = 12
) -> HistoricalReport:
    closures = closures_repo.list_closures_for_branch(engine, idsucursal, months)
    details = closures_repo.get_branch_detail_history(engine, idsucursal, months)
    auditor_stats = auditors_repo.get_auditor_stats_for_branch(engine, idsucursal, months)

    ctx = HistoricalContext(
        idsucursal=idsucursal,
        months_back=months,
        closures=closures,
        details=details,
        auditor_stats=auditor_stats,
    )
    findings = run_all_historical(ctx)
    ranked = rank_findings(findings)
    return HistoricalReport(
        idsucursal=idsucursal,
        months_back=months,
        closures_analyzed=int(len(closures)),
        findings=ranked,
        summary_by_severity=summarize_by_severity(ranked),
        summary_by_category=summarize_by_category(ranked),
    )


def _opt_int(v) -> int | None:
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return int(v)
