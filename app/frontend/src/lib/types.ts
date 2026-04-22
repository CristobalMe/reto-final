export type Severity = "CRITICA" | "ALTA" | "MEDIA" | "BAJA";

export interface BackendFinding {
  metric_id: string;
  severity: Severity;
  category: string;
  message: string;
  score: number;

  idproducto: number | null;
  product_name: string | null;
  categoria_nombre: string | null;

  value_mxn: number;
  pct_variance: number | null;
  diferencia: number | null;

  idsucursal: number | null;
  idauditor: number | null;
  idinventariomes: number | null;

  extra: Record<string, unknown>;
}

export interface ClosureHeader {
  idinventariomes: number;
  idsucursal: number;
  idalmacen: number;
  idauditor: number | null;
  idusuario: number;
  fecha: string | null;
  estatus: string;
  total: number;
  faltantes: number;
  sobrantes: number;
  total_fisico: number;
  almacen_nombre: string | null;
  almacen_encargado: string | null;
}

export interface ProductContext {
  idproducto: number;
  producto_nombre: string;
  producto_clase: string | null;
  unidad: string | null;
  categoria_nombre: string | null;
  subcategoria_nombre: string | null;
  stockinicial: number;
  stockteorico: number;
  stockfisico: number;
  diferencia: number;
  difimporte: number;
  costopromedio: number;
  ingresocompra: number;
  ingresoordentablajeria: number;
  egresoventa: number;
  egresoordentablajeria: number;
  egresodevolucion: number;
  aclaracion: string | null;
}

export interface SeveritySummary {
  severity: Severity;
  count: number;
  total_impact_mxn: number;
}

export interface CategorySummary {
  category: string;
  count: number;
  total_impact_mxn: number;
}

export interface LocalReport {
  idinventariomes: number;
  header: ClosureHeader | null;
  findings: BackendFinding[];
  summary_by_severity: SeveritySummary[];
  summary_by_category: CategorySummary[];
  context_by_idproducto: Record<string, ProductContext>;
}

export interface ClosureListItem {
  idinventariomes: number;
  idsucursal: number;
  idalmacen: number;
  idauditor: number | null;
  idusuario: number;
  fecha: string | null;
  estatus: string;
  total: number;
  faltantes: number;
  sobrantes: number;
  almacen_nombre: string | null;
  almacen_encargado: string | null;
}

/** Shape consumed by dashboard components (normalised from backend). */
export type AlertTipo = "loss" | "surplus" | "missing";
export type AlertSeverity = "high" | "mid" | "low";
export type ProductCategoryKey = "alimentos" | "bebidas" | "miscelaneos" | "otros";

export interface DashboardAlert {
  id: string;                         // metric_id + idproducto (stable)
  metric_id: string;
  backend_category: string;
  message: string;
  score: number;

  idinventariomes: number | null;
  idproducto: number | null;
  idsucursal: number | null;
  idalmacen: number;
  idauditor: number | null;

  producto_nombre: string;
  producto_clase: string;
  producto_unidad: string;
  producto_cat: ProductCategoryKey;
  producto_cat_nombre: string;

  almacen_nombre: string;
  almacen_encargado: string;
  inventariomes_fecha: Date | null;

  diferencia: number;
  difimporte: number;
  costopromedio: number;
  stockteorico: number;
  stockfisico: number;
  stockinicial: number;
  ingresocompra: number;
  ingresoordentablajeria: number;
  egresoventa: number;
  egresoordentablajeria: number;

  aclaracion: string;

  tipo: AlertTipo;
  severity: AlertSeverity;
  severity_label: Severity;
  revisada: boolean;
}
