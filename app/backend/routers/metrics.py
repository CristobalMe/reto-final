from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Engine

from db import get_engine
from domain.models import HistoricalReport, LocalReport, MetricCatalogEntry
from metrics.registry import catalog
from services.metrics_service import compute_historical_report, compute_local_report

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/catalog", response_model=list[MetricCatalogEntry])
def get_catalog():
    return catalog()


@router.get("/local/{idinventariomes}", response_model=LocalReport)
def local_report(
    idinventariomes: int,
    engine: Engine = Depends(get_engine),
):
    report = compute_local_report(engine, idinventariomes)
    if report.header is None:
        raise HTTPException(status_code=404, detail=f"Closure {idinventariomes} not found")
    return report


@router.get("/historical/branch/{idsucursal}", response_model=HistoricalReport)
def historical_branch_report(
    idsucursal: int,
    months: int = 12,
    engine: Engine = Depends(get_engine),
):
    if months < 1 or months > 60:
        raise HTTPException(status_code=400, detail="months must be between 1 and 60")
    return compute_historical_report(engine, idsucursal, months)
