import pandas as pd

from metrics.base import HistoricalContext
from metrics.historical.h01_recurring_shortage import H01RecurringShortage
from metrics.historical.h02_branch_zscore import H02BranchZScore


def test_h01_flags_three_consecutive_shortages():
    details = pd.DataFrame([
        {"idinventariomes": 1, "idproducto": 99, "producto_nombre": "X", "categoria_nombre": "Bebidas",
         "fecha": "2026-01-01", "idauditor": 1, "stockteorico": 10, "stockfisico": 8,
         "diferencia": -2, "difimporte": -200, "costopromedio": 100},
        {"idinventariomes": 2, "idproducto": 99, "producto_nombre": "X", "categoria_nombre": "Bebidas",
         "fecha": "2026-02-01", "idauditor": 1, "stockteorico": 10, "stockfisico": 7,
         "diferencia": -3, "difimporte": -300, "costopromedio": 100},
        {"idinventariomes": 3, "idproducto": 99, "producto_nombre": "X", "categoria_nombre": "Bebidas",
         "fecha": "2026-03-01", "idauditor": 1, "stockteorico": 10, "stockfisico": 6,
         "diferencia": -4, "difimporte": -400, "costopromedio": 100},
    ])
    ctx = HistoricalContext(
        idsucursal=1, months_back=12,
        closures=pd.DataFrame(), details=details, auditor_stats=pd.DataFrame(),
    )
    findings = H01RecurringShortage().compute(ctx)
    assert len(findings) == 1
    assert findings[0].severity == "CRITICA"
    assert findings[0].extra["consecutive_shortages"] == 3


def test_h02_flags_outlier_closure():
    # Seven closures with one clear outlier
    closures = pd.DataFrame([
        {"idinventariomes": i, "faltantes": 100, "idauditor": 1} for i in range(1, 7)
    ] + [{"idinventariomes": 99, "faltantes": 5000, "idauditor": 1}])
    ctx = HistoricalContext(
        idsucursal=1, months_back=12,
        closures=closures, details=pd.DataFrame(), auditor_stats=pd.DataFrame(),
    )
    findings = H02BranchZScore().compute(ctx)
    assert any(f.idinventariomes == 99 for f in findings)
