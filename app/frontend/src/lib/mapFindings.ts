import type {
  BackendFinding,
  ClosureHeader,
  ProductContext,
  DashboardAlert,
  AlertTipo,
  AlertSeverity,
  ProductCategoryKey,
  Severity,
} from './types';

const MISSING_CATEGORIES = new Set(['MISSING_COUNT', 'FABRICATED_COUNT', 'SOD_VIOLATION']);

function toTipo(f: BackendFinding): AlertTipo {
  if (MISSING_CATEGORIES.has(f.category)) return 'missing';
  if ((f.value_mxn ?? 0) > 0) return 'surplus';
  return 'loss';
}

function toSeverity(s: Severity): AlertSeverity {
  if (s === 'CRITICA' || s === 'ALTA') return 'high';
  if (s === 'MEDIA') return 'mid';
  return 'low';
}

function toCatKey(s: string | null | undefined): ProductCategoryKey {
  const lower = (s ?? '').toLowerCase();
  if (lower.includes('bebida')) return 'bebidas';
  if (lower.includes('aliment') || lower.includes('carne') || lower.includes('pollo')) return 'alimentos';
  if (lower.includes('misc')) return 'miscelaneos';
  return 'otros';
}

export function mapFindings(
  findings: BackendFinding[],
  context: Record<string, ProductContext>,
  header: ClosureHeader,
): DashboardAlert[] {
  return findings.map((f) => {
    const ctx = f.idproducto != null ? context[String(f.idproducto)] : null;
    return {
      id: `${f.metric_id}-${f.idproducto ?? 'null'}`,
      metric_id: f.metric_id,
      backend_category: f.category,
      message: f.message,
      score: f.score,

      idinventariomes: f.idinventariomes,
      idproducto: f.idproducto,
      idsucursal: f.idsucursal,
      idalmacen: header.idalmacen,
      idauditor: f.idauditor ?? header.idauditor,

      producto_nombre: ctx?.producto_nombre ?? f.product_name ?? '—',
      producto_clase: ctx?.producto_clase ?? '—',
      producto_unidad: ctx?.unidad ?? '—',
      producto_cat: toCatKey(f.categoria_nombre ?? ctx?.categoria_nombre),
      producto_cat_nombre: f.categoria_nombre ?? ctx?.categoria_nombre ?? '—',

      almacen_nombre: header.almacen_nombre ?? '—',
      almacen_encargado: header.almacen_encargado ?? '—',
      inventariomes_fecha: header.fecha ? new Date(header.fecha) : null,

      diferencia: ctx?.diferencia ?? f.diferencia ?? 0,
      difimporte: ctx?.difimporte ?? f.value_mxn ?? 0,
      costopromedio: ctx?.costopromedio ?? 0,
      stockteorico: ctx?.stockteorico ?? 0,
      stockfisico: ctx?.stockfisico ?? 0,
      stockinicial: ctx?.stockinicial ?? 0,
      ingresocompra: ctx?.ingresocompra ?? 0,
      ingresoordentablajeria: ctx?.ingresoordentablajeria ?? 0,
      egresoventa: ctx?.egresoventa ?? 0,
      egresoordentablajeria: ctx?.egresoordentablajeria ?? 0,

      aclaracion: ctx?.aclaracion ?? '',

      tipo: toTipo(f),
      severity: toSeverity(f.severity),
      severity_label: f.severity,
      revisada: false,
    };
  });
}
