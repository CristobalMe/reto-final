# Copiloto Analítico TALOS — Cierre de Semana

Sistema de detección de anomalías en cierres de inventario para AERSA. Lee los registros de `inventariomes` de la base MySQL de TALOS, corre 11 métricas locales por cierre y 4 métricas históricas por sucursal, y expone los hallazgos a través de un dashboard web.

## Estructura del repo

```
reto-final/
├── app/
│   ├── backend/          FastAPI + motor de métricas
│   └── frontend/         Next.js dashboard
├── ab-testing-package/   Paquete npm `auto-ab` (epsilon-greedy A/B)
├── data/talos_tecmty/    Dumps SQL de la BD de producción (gitignored en prod)
├── deployment/mysql/     Configuración de MySQL para Docker
├── notebooks/            Análisis exploratorio y validación de reglas
└── docker-compose.yml
```

## Requisitos

- Docker y Docker Compose
- Node.js ≥18 (solo para desarrollo del paquete `auto-ab`)
- Python ≥3.11 (solo para desarrollo del backend fuera de Docker)

## Correr todo con Docker

```bash
# Primera vez — importa ~2 GB de datos (puede tardar 5-10 min)
docker compose up -d

# Ver logs del proceso de importación de MySQL
docker compose logs -f mysql

# Una vez levantado:
#   Frontend → http://localhost:3000
#   Backend  → http://localhost:8000
#   MySQL    → 127.0.0.1:3307 (usuario: root, contraseña: root)
```

Puertos por defecto:

| Servicio  | Puerto host |
|-----------|-------------|
| MySQL     | 3307        |
| Backend   | 8000        |
| Frontend  | 3000        |

El puerto 3307 (no 3306) evita colisiones con instalaciones locales de MySQL.

Para cambiar la contraseña o el puerto de MySQL, crea un `.env` en la raíz:

```env
MYSQL_ROOT_PASSWORD=mipassword
MYSQL_PORT=3308
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Desarrollo con hot-reload

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

El frontend corre en modo `next dev`. El backend monta `./app/backend` como bind mount y usa `--reload` de uvicorn, por lo que un cambio en cualquier `.py` reinicia el servidor automáticamente.

### Reiniciar la base de datos desde cero

```bash
docker compose down -v       # borra el volumen
docker compose up -d mysql   # reimporta
```

### Verificar la importación

```bash
docker compose exec -T mysql mysql -uroot -proot -D talos_tecmty -e "
  SELECT COUNT(*) AS inventariomes    FROM inventariomes;
  SELECT COUNT(*) AS inventariomesdetalle FROM inventariomesdetalle;
  SELECT COUNT(*) AS producto         FROM producto;
"
```

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│  Next.js frontend (port 3000)                           │
│  AlertDashboard → /closures + /metrics/local/{id}       │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────────┐
│  FastAPI backend (port 8000)                            │
│                                                         │
│  GET /closures          lista cierres recientes         │
│  GET /metrics/local/{id}  hallazgos de un cierre        │
│  GET /metrics/historical/branch/{id}  historial         │
│  GET /metrics/catalog   catálogo de métricas            │
│  GET /health                                            │
└────────────────────────┬────────────────────────────────┘
                         │ SQLAlchemy / pymysql
┌────────────────────────▼────────────────────────────────┐
│  MySQL 8.0 (port 3307)                                  │
│  base: talos_tecmty                                     │
│  tablas clave: inventariomes, inventariomesdetalle,     │
│                producto, almacen, categoria             │
└─────────────────────────────────────────────────────────┘
```

El backend no tiene estado entre requests. Cada llamada a `/metrics/local/{id}` corre todas las métricas locales sobre el DataFrame de ese cierre y regresa un `LocalReport` completo.

## Qué hacen las métricas

El motor corre dos tipos de métricas:

**Locales** — operan sobre las líneas de un solo cierre (`inventariomesdetalle`):

| ID  | Nombre                              | Categoría               | Umbral relevante |
|-----|-------------------------------------|-------------------------|------------------|
| R01 | Faltante significativo              | SHORTAGE                | >$800 MXN (Alimentos), >$500 (Bebidas) |
| R02 | Sobrante significativo              | SURPLUS                 | >$800 MXN (Alimentos) |
| R03 | Variación % elevada vs teórico      | VARIANCE                | >15% ALTA, >30% CRÍTICA |
| R04 | Caída de stock sin ventas           | UNREGISTERED_CONSUMPTION | stock bajó ≥1 unidad, egresoventa=0 |
| R05 | Compra sin consumo                  | PURCHASE_NO_CONSUMPTION  | ingresocompra>0, egresoventa=0 |
| R06 | Reajuste manual elevado             | MANUAL_ADJUSTMENT        | >10% del stock teórico |
| R07 | Merma excesiva                      | WASTE_EXCESS             | — |
| R08 | Sin conteo físico                   | MISSING_COUNT            | stockfisico=null, stockteorico>0 |
| R09 | Conteo físico sospechosamente redondo | FABRICATED_COUNT       | stockfisico múltiplo exacto de 100/50/10 |
| R10 | Violación de segregación de funciones | SOD_VIOLATION          | idauditor == idusuario |
| R11 | Costo atípico                       | COST_OUTLIER             | — |

**Históricas** — operan sobre múltiples cierres de una sucursal:

| ID  | Nombre                          | Categoría        |
|-----|----------------------------------|------------------|
| H01 | Faltante recurrente              | RECURRING_SHORTAGE — ≥3 cierres consecutivos con faltante ≤−$100 |
| H02 | Z-score de la sucursal           | BRANCH_OUTLIER — \|z\|≥2.0 ALTA, \|z\|≥3.0 CRÍTICA (requiere ≥6 muestras) |
| H03 | Concentración de auditor         | AUDITOR_CONCENTRATION |
| H04 | Persistencia producto-sucursal   | PRODUCT_PERSISTENCE |

### Score de prioridad

Cada hallazgo recibe un score en [0, 1]:

```
score = 0.65 × (|value_mxn| / max_mxn)
      + 0.25 × (peso_severidad / 4)
      + 0.10 × meta_component
```

`meta_component` escala el número de cierres consecutivos (H01) o el `pct_variance` (R03) para que los hallazgos recurrentes suban en el ranking.

Los hallazgos se ordenan primero por severidad (`CRITICA > ALTA > MEDIA > BAJA`), luego por score.

## Esquema de la base de datos

Las dos tablas centrales:

**`inventariomes`** — encabezado de cada cierre de inventario
- `idinventariomes` PK
- `idsucursal`, `idalmacen`, `idusuario`, `idauditor`
- `inventariomes_fecha` — datetime del cierre
- `inventariomes_faltantes`, `inventariomes_sobrantes` — totales monetarios
- `inventariomes_estatus` — enum: `generando/finalizado/error/editando/aplicado/terminado`

**`inventariomesdetalle`** — una fila por producto en el cierre
- `inventariomesdetalle_stockinicial` — stock al inicio del período
- `inventariomesdetalle_stockteorico` — stock calculado (inicial ± movimientos)
- `inventariomesdetalle_stockfisico` — conteo físico real
- `inventariomesdetalle_diferencia` — teórico − físico
- `inventariomesdetalle_difimporte` — diferencia × costo promedio (MXN)
- `inventariomesdetalle_reajuste` — ajuste manual aplicado por el operador
- Entradas: `ingresocompra`, `ingresorequisicion`, `ingresoordentablajeria`
- Salidas: `egresoventa`, `egresorequisicion`, `egresoordentablajeria`, `egresodevolucion`

## Subproyectos

- [`app/backend/`](app/backend/) — FastAPI, motor de métricas, repositorios SQL
- [`app/frontend/`](app/frontend/) — Next.js dashboard
- [`ab-testing-package/`](ab-testing-package/) — paquete `auto-ab` (epsilon-greedy A/B testing para React)
