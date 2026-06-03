# Backend — Talos Fraud Metrics API

FastAPI sobre MySQL. Lee los datos de cierre de inventario de TALOS y corre el motor de métricas.

## Correr en desarrollo

```bash
# Con Docker (recomendado — ver README raíz)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d backend

# Sin Docker
pip install -r requirements.txt

# Variables de entorno (o crear .env)
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3307
export MYSQL_USER=root
export MYSQL_ROOT_PASSWORD=root
export MYSQL_DATABASE=talos_tecmty

uvicorn main:app --reload --port 8000
```

## Variables de entorno

| Variable              | Default      | Descripción |
|-----------------------|-------------|-------------|
| `MYSQL_HOST`          | `127.0.0.1` | Host de MySQL |
| `MYSQL_PORT`          | `3307`      | Puerto |
| `MYSQL_USER`          | `root`      | Usuario |
| `MYSQL_ROOT_PASSWORD` | `root`      | Contraseña |
| `MYSQL_DATABASE`      | `talos_tecmty` | Base de datos |
| `CORS_ORIGINS`        | `["http://localhost:3000"]` | Lista JSON de orígenes permitidos |

## API

### `GET /health`
Siempre regresa `{"status": "ok"}`. Usado por Docker healthcheck.

---

### `GET /closures`
Lista cierres en estatus cerrado (`finalizado`, `aplicado`, `terminado`).

Query params:
- `idsucursal` (opcional) — filtra por sucursal
- `months` (1–60, default 3) — ventana de tiempo hacia atrás
- `limit` (1–500, default 50) — máximo de resultados

Respuesta: array de objetos con `idinventariomes`, `idsucursal`, `idalmacen`, `idauditor`, `idusuario`, `fecha`, `estatus`, `total`, `faltantes`, `sobrantes`, `almacen_nombre`, `almacen_encargado`.

---

### `GET /metrics/catalog`
Regresa el catálogo completo de métricas registradas: `id`, `name`, `description`, `scope` (LOCAL|HISTORICAL), `category`, `severity_hint`.

---

### `GET /metrics/local/{idinventariomes}`
Corre todas las métricas locales sobre el cierre especificado.

Respuesta `LocalReport`:
```json
{
  "idinventariomes": 118888,
  "header": { "idsucursal": ..., "idalmacen": ..., "fecha": "...", "faltantes": -1234.56, ... },
  "findings": [
    {
      "metric_id": "R01",
      "severity": "CRITICA",
      "category": "SHORTAGE",
      "message": "Faltante crítico: $-3,200.00 MXN.",
      "score": 0.8312,
      "idproducto": 42,
      "product_name": "Ron Bacardi 750ml",
      "value_mxn": -3200.0,
      "diferencia": -8.0
    }
  ],
  "summary_by_severity": [{ "severity": "CRITICA", "count": 3, "total_impact_mxn": -9600.0 }],
  "summary_by_category": [...],
  "context_by_idproducto": {
    "42": { "stockinicial": 24.0, "stockteorico": 22.0, "stockfisico": 14.0, ... }
  }
}
```

404 si el cierre no existe.

---

### `GET /metrics/historical/branch/{idsucursal}`
Corre las métricas históricas para todos los cierres de la sucursal en la ventana dada.

Query params:
- `months` (1–60, default 12)

Respuesta `HistoricalReport`:
```json
{
  "idsucursal": 13,
  "months_back": 12,
  "closures_analyzed": 47,
  "findings": [...],
  "summary_by_severity": [...],
  "summary_by_category": [...]
}
```

---

## Estructura de archivos

```
backend/
├── main.py               Lifespan (seed), CORS, routers
├── config.py             Settings via pydantic-settings (.env)
├── db.py                 SQLAlchemy engine (singleton)
├── schema.sql            DDL de las 7 tablas
├── seed.sql              Datos del cierre 118888 para demo
│
├── domain/
│   └── models.py         Pydantic models: Finding, LocalReport, HistoricalReport, ...
│
├── routers/
│   ├── closures.py       GET /closures
│   └── metrics.py        GET /metrics/*
│
├── services/
│   ├── metrics_service.py  Orquesta repositorios + métricas + scoring
│   └── scoring_service.py  rank_findings(), summarize_by_*()
│
├── repositories/
│   ├── closures.py       get_closure_header(), get_closure_detail(), list_closures_for_branch()
│   ├── auditors.py       get_auditor_stats_for_branch()
│   └── products.py       helpers de producto
│
└── metrics/
    ├── base.py           BaseMetric, LocalMetric, HistoricalMetric, HistoricalContext
    ├── registry.py       Registro global (@register_local, @register_historical)
    ├── local/
    │   ├── _helpers.py   make_finding(), cat_value()
    │   ├── r01_shortage.py
    │   ├── r02_surplus.py
    │   ├── r03_variance_pct.py
    │   ├── r04_stock_drop_no_sales.py
    │   ├── r05_purchase_no_consumption.py
    │   ├── r06_high_adjustments.py
    │   ├── r07_waste_excess.py
    │   ├── r08_no_physical_count.py
    │   ├── r09_round_number_count.py
    │   ├── r10_segregation_duties.py
    │   └── r11_cost_outlier.py
    └── historical/
        ├── h01_recurring_shortage.py
        ├── h02_branch_zscore.py
        ├── h03_auditor_concentration.py
        └── h04_product_branch_persistence.py
```

## Agregar una nueva métrica

1. Crea un archivo en `metrics/local/` o `metrics/historical/`.
2. Define una clase que herede de `LocalMetric` o `HistoricalMetric`.
3. Decora con `@register_local` o `@register_historical`.
4. Rellena el campo `meta: MetricMeta` con `id`, `name`, `description`, `category`, `severity_hint`.
5. Implementa `compute(self, df, header)` → `list[Finding]`.

El registro ocurre en tiempo de importación; `main.py` importa el paquete `metrics` con `import metrics` para disparar todos los `__init__.py`, que a su vez importan cada módulo.

## Scoring

```python
score = 0.65 * (abs(value_mxn) / max_mxn_in_report)
      + 0.25 * (severity_weight / 4)        # CRITICA=4, ALTA=3, MEDIA=2, BAJA=1
      + 0.10 * meta_component               # recurrencia o pct_variance normalizado
```

Los hallazgos se ordenan por `(severity_weight DESC, score DESC)` antes de devolverse.

## Tests

```bash
cd app/backend
pytest tests/
```

Los tests de métricas locales e históricas usan DataFrames construidos in-memory (sin base de datos).
