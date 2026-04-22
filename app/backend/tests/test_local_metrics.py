import pandas as pd

from metrics.local.r01_shortage import R01Shortage
from metrics.local.r02_surplus import R02Surplus
from metrics.local.r06_high_adjustments import R06HighAdjustments
from metrics.local.r09_round_number_count import R09RoundNumberCount
from metrics.local.r10_segregation_duties import R10SegregationOfDuties


def _row(**overrides) -> dict:
    base = {
        "idproducto": 1,
        "producto_nombre": "TEST",
        "categoria_nombre": "Bebidas",
        "stockinicial": 10.0,
        "stockteorico": 10.0,
        "stockfisico": 10.0,
        "diferencia": 0.0,
        "ingresocompra": 0.0,
        "ingresorequisicion": 0.0,
        "egresorequisicion": 0.0,
        "egresoventa": 0.0,
        "reajuste": 0.0,
        "egresodevolucion": 0.0,
        "costopromedio": 50.0,
        "difimporte": 0.0,
        "producto_costo_ref": 50.0,
    }
    base.update(overrides)
    return base


def test_r01_flags_critical_shortage_in_bebidas():
    df = pd.DataFrame([_row(difimporte=-2500, diferencia=-50)])
    findings = R01Shortage().compute(df, header={})
    assert len(findings) == 1
    assert findings[0].severity == "CRITICA"


def test_r01_ignores_small_shortages():
    df = pd.DataFrame([_row(difimporte=-100, diferencia=-2)])
    assert R01Shortage().compute(df, header={}) == []


def test_r02_flags_high_surplus():
    df = pd.DataFrame([_row(difimporte=1500, diferencia=30)])
    findings = R02Surplus().compute(df, header={})
    assert len(findings) == 1
    assert findings[0].severity == "ALTA"


def test_r06_flags_large_adjustments():
    df = pd.DataFrame([_row(reajuste=5.0, stockteorico=20.0)])
    findings = R06HighAdjustments().compute(df, header={})
    assert len(findings) == 1
    # reajuste = 25% of stockteorico > 10% default threshold


def test_r09_flags_round_numbers():
    df = pd.DataFrame([_row(stockfisico=100.0, stockteorico=87.3)])
    findings = R09RoundNumberCount().compute(df, header={})
    assert len(findings) == 1


def test_r10_flags_same_auditor_and_user():
    df = pd.DataFrame([_row()])
    header = {"idauditor": 42, "idusuario": 42, "idinventariomes": 1, "idsucursal": 9, "faltantes": -100}
    findings = R10SegregationOfDuties().compute(df, header)
    assert len(findings) == 1
    assert findings[0].severity == "CRITICA"


def test_r10_clean_when_different_users():
    df = pd.DataFrame([_row()])
    header = {"idauditor": 42, "idusuario": 7, "idinventariomes": 1, "idsucursal": 9, "faltantes": 0}
    assert R10SegregationOfDuties().compute(df, header) == []
