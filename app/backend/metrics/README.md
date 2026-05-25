# Metrics Specifications

This document defines all metrics available in the metrics module. Metrics are categorized into two types:

- **Historical Metrics**: Analyze patterns across multiple closures to identify trends and anomalies
- **Local Metrics**: Analyze individual closure data to identify immediate issues

---

## Metrics Summary

| ID | Name | Description | Severity | Scope |
|---|---|---|---|---|
| **H01** | Faltante Recurrente | Product shows shortages in N or more consecutive closures at the same branch | 🔴 CRÍTICA | Product-Branch historical |
| **H02** | Z-score de Cierres | Closure total shortage is statistically anomalous vs branch history | 🟠 ALTA | Branch historical |
| **H03** | Concentración por Auditor | Auditor's closures show higher shortages than peers or frequent self-captures | 🟠 ALTA | Auditor historical |
| **R01** | Faltante Significativo | Product shortage exceeds category-specific MXN cutoffs | 🟠 ALTA | Single closure, per-product |
| **R02** | Sobrante Significativo | Product surplus exceeds category cutoffs | 🟠 ALTA | Single closure, per-product |
| **R03** | Variación % Elevada | Percent difference between physical and theoretical stock exceeds threshold | 🟠 ALTA  | Single closure, per-product |
| **R04** | Stock Drop sin Ventas | Stock decreases without sales recorded (unregistered consumption) | 🟡 MEDIA | Single closure, per-product |
| **R05** | Compra sin Consumo | Purchase recorded with negligible consumption | 🟡 MEDIA | Single closure, per-product |
| **R06** | Reajuste Manual Elevado | Manual adjustment exceeds X% of theoretical stock | 🟠 ALTA | Single closure, per-product |
| **R07** | Devolución / Merma Excesiva | Returns or waste exceed X% of theoretical stock | 🟠 ALTA | Single closure, per-product |
| **R08** | Sin Conteo Físico | Physical count is zero with significant theoretical stock and movement | 🟡 MEDIA | Single closure, per-product |
| **R09** | Conteo Sospechosamente Redondo | Physical count is exact round number while theoretical differs significantly | 🟡 MEDIA | Single closure, per-product |
| **R10** | Sin Segregación de Funciones | Auditor and capture user are the same person (SOD violation) | 🔴 CRÍTICA | Closure header identity |
| **R11** | Costo Promedio Anómalo | Average cost deviates from reference cost by more than X% | 🟡 MEDIA | Single closure, per-product |

---

## Historical Metrics

Historical metrics operate across many closures for a branch, product, or auditor, analyzing patterns over time.

### H01: Recurring Shortage
**Faltante Recurrente**

**Description:** Identifies products showing shortages in N or more consecutive closures at the same branch.

**Category:** `RECURRING_SHORTAGE`  
**Severity:** 🔴 CRÍTICA  
**Scope:** Product-Branch historical analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_consecutive_shortages` | 3 | Number of consecutive closure shortages required to flag |
| `min_shortage_mxn` | -100.0 | Minimum monetary value (MXN) to classify as a shortage event |

---

### H02: Branch Z-Score
**Z-score de Cierres de la Sucursal**

**Description:** Flags closures whose total shortage is statistically anomalous compared to the branch's own historical performance. Uses standard deviation analysis to identify outliers.

**Category:** `BRANCH_OUTLIER`  
**Severity:** 🟠 ALTA  
**Scope:** Branch historical closure analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `z_high` | 2.0 | Z-score threshold for ALTA severity |
| `z_critical` | 3.0 | Z-score threshold for CRÍTICA severity |
| `min_samples` | 6 | Minimum number of historical closures required for analysis |

**Severity Mapping:**
- **CRÍTICA:** Z-score ≥ 3.0 or ≤ -3.0
- **ALTA:** Z-score ≥ 2.0 or ≤ -2.0

---

### H03: Auditor Concentration
**Concentración de Variance por Auditor**

**Description:** Identifies auditors whose closures in a branch show consistently higher shortages than peers, or who frequently close their own captures (potential self-interest bias).

**Category:** `AUDITOR_OUTLIER`  
**Severity:** 🟠 ALTA  
**Scope:** Auditor historical performance analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_closures` | 3 | Minimum number of closures required for auditor to be analyzed |
| `z_high` | 1.5 | Z-score threshold relative to peer performance |
| `self_closure_share_high` | 0.5 | Threshold for percentage of self-captured closures (50%) |

---

## Local Metrics

Local metrics operate on individual closure data, analyzing line-item details within a single closure event.

### R01: Significant Shortage
**Faltante Significativo**

**Description:** Flags products whose monetary shortage exceeds category-specific thresholds. Identifies immediate inventory discrepancies requiring attention.

**Category:** `SHORTAGE`  
**Severity:** 🟠 ALTA  
**Scope:** Single closure, per-product analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| **Critical Thresholds (CRÍTICA):** | | |
| `critical_mxn[Bebidas]` | -2,000 | Critical shortage threshold for Beverages category |
| `critical_mxn[Alimentos]` | -3,000 | Critical shortage threshold for Food category |
| `critical_mxn[Gastos]` | -5,000 | Critical shortage threshold for Expenses category |
| `critical_mxn[_default]` | -3,000 | Default critical threshold for unmapped categories |
| **High Thresholds (ALTA):** | | |
| `high_mxn[Bebidas]` | -500 | High shortage threshold for Beverages category |
| `high_mxn[Alimentos]` | -800 | High shortage threshold for Food category |
| `high_mxn[Gastos]` | -1,500 | High shortage threshold for Expenses category |
| `high_mxn[_default]` | -800 | Default high threshold for unmapped categories |
| **Units Fallback:** | | |
| `unit_fallback_min_units` | 2.0 | Minimum units for fallback when cost data is unavailable |

---

### R02: Significant Surplus
**Sobrante Significativo**

**Description:** Flags products whose monetary surplus exceeds category-specific thresholds. May indicate inventory stuffing, mis-counted theoretical stock, or data entry errors.

**Category:** `SURPLUS`  
**Severity:** 🟠 ALTA  
**Scope:** Single closure, per-product analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `high_mxn[Bebidas]` | 500 | Surplus threshold for Beverages category |
| `high_mxn[Alimentos]` | 800 | Surplus threshold for Food category |
| `high_mxn[Gastos]` | 1,500 | Surplus threshold for Expenses category |
| `high_mxn[_default]` | 800 | Default surplus threshold for unmapped categories |

---

### R03: High Percentage Variance
**Variación % Elevada vs Stock Teórico**

**Description:** Flags products where the percentage difference between physical and theoretical stock exceeds thresholds. Indicates significant inventory discrepancies.

**Category:** `VARIANCE`  
**Severity:** 🟠 ALTA 
**Scope:** Single closure, per-product analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `pct_high` | 15.0 | Percentage variance threshold for ALTA severity |
| `pct_critical` | 30.0 | Percentage variance threshold for CRÍTICA severity |
| `min_stockteorico` | 1.0 | Minimum theoretical stock to analyze (units) |
| `min_abs_diferencia` | 0.5 | Minimum absolute difference to report (units) |

**Severity Mapping:**
- **CRÍTICA:** Variance ≥ 30% or ≤ -30%
- **ALTA:** Variance ≥ 15% or ≤ -15%

---

### R04: Stock Drop Without Sales
**Caída de Stock sin Ventas Registradas**

**Description:** Flags products where theoretical stock decreases meaningfully without corresponding sales records. Suggests unregistered consumption, theft, or administrative errors.

**Category:** `UNREGISTERED_CONSUMPTION`  
**Severity:** 🟡 MEDIA  
**Scope:** Single closure, per-product analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_stock_drop_units` | 1.0 | Minimum stock drop in units to flag |
| `max_sales_tolerance` | 0.0 | Maximum recorded sales to classify as "no sales" |

---

### R05: Purchase Without Consumption
**Compra sin Consumo**

**Description:** Flags products where purchase was recorded with negligible consumption. May indicate unauthorized diversion, data entry error, or inventory tampering.

**Category:** `UNUSED_PURCHASE`  
**Severity:** 🟡 MEDIA  
**Scope:** Single closure, per-product analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_purchase_units` | 2.0 | Minimum purchase quantity to analyze (units) |
| `consumption_pct_cutoff` | 5.0 | Consumption must be below this percentage of purchase to flag |

---

### R06: High Manual Adjustments
**Reajuste Manual Elevado**

**Description:** Flags manual adjustments (reajustes) exceeding a percentage of theoretical stock. May indicate audit-trail tampering or data corrections.

**Category:** `MANUAL_ADJUSTMENT`  
**Severity:** 🟠 ALTA  
**Scope:** Single closure, per-product analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `reajuste_pct` | 10.0 | Adjustment threshold as percentage of theoretical stock |
| `min_stockteorico` | 1.0 | Minimum theoretical stock to analyze (units) |

---

### R07: Waste or Excessive Returns
**Devolución / Merma Excesiva**

**Description:** Flags excessive returns or waste that exceed a percentage of theoretical stock. May conceal actual shrinkage or inventory issues.

**Category:** `WASTE`  
**Severity:** 🟠 ALTA  
**Scope:** Single closure, per-product analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `devolucion_pct` | 5.0 | Return/waste threshold as percentage of theoretical stock |
| `min_stockteorico` | 1.0 | Minimum theoretical stock to analyze (units) |

---

### R08: No Physical Count
**Sin Conteo Físico**

**Description:** Flags products where physical count is zero while theoretical stock and movement are significant. Indicates a likely missed physical inventory count.

**Category:** `MISSING_COUNT`  
**Severity:** 🟡 MEDIA  
**Scope:** Single closure, per-product analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_stockteorico` | 5.0 | Minimum theoretical stock to flag as missed count (units) |
| `min_movement_abs` | 0.1 | Minimum absolute movement to require (units) |

---

### R09: Suspiciously Round Count
**Conteo Físico Sospechosamente Redondo**

**Description:** Flags physical counts that are exact multiples of round numbers (100, 50, 10) while theoretical stock differs significantly. Suggests a fabricated or estimated count.

**Category:** `FABRICATED_COUNT`  
**Severity:** 🟡 MEDIA  
**Scope:** Single closure, per-product analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `round_multiples` | (100.0, 50.0, 10.0) | List of round number multiples to check for |
| `min_stockfisico` | 10.0 | Minimum physical stock to analyze (units) |
| `min_theoretical_gap` | 2.0 | Minimum difference between theoretical and physical stock to flag |

---

### R10: Segregation of Duties Violation
**Sin Segregación de Funciones**

**Description:** **CRITICAL CONTROL VIOLATION** — The auditor and the user who captured the closure are the same person (idauditor == idusuario). Violates fundamental segregation of duties control.

**Category:** `SOD_VIOLATION`  
**Severity:** 🔴 CRÍTICA  
**Scope:** Closure header-level identity check

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| (None - Rule-based) | — | Triggers when `idauditor == idusuario` |

**Control Impact:** This is a **compliance violation**. The same individual should not both capture and audit the same closure to prevent fraud opportunities.

---

### R11: Anomalous Reference Cost
**Costo Promedio Anómalo vs Catálogo**

**Description:** Flags products where the average unit cost deviates from the product's reference catalog cost by more than a threshold. May indicate mis-pricing, mis-posted receipts, or data errors.

**Category:** `COST_ANOMALY`  
**Severity:** 🟡 MEDIA  
**Scope:** Single closure, per-product analysis

**Thresholds:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `deviation_pct` | 40.0 | Maximum allowed deviation from reference cost (percentage) |
| `min_reference_cost` | 1.0 | Minimum reference cost to analyze (MXN) |

---

## Implementation Notes

- **Severity Levels:**
  - 🔴 **CRÍTICA** (Critical): Immediate action required
  - 🟠 **ALTA** (High): Review and investigate
  - 🟡 **MEDIA** (Medium): Monitor and track

- **Data Requirements:**
  - Historical metrics require sufficient historical data (see `min_samples` thresholds)
  - All monetary values are in Mexican Pesos (MXN)
  - Category mapping is performed via `categoria_nombre` field

- **Performance Considerations:**
  - Local metrics run per-closure with O(n) complexity per product
  - Historical metrics aggregate across closures and may require significant data processing


