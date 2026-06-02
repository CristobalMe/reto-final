import type { MetricsRecord, VariantStats } from "../types.js";

export function serializeRecord(r: MetricsRecord): string {
  return JSON.stringify(r);
}

export function parseStats(records: MetricsRecord[]): VariantStats[] {
  const map = new Map<string, { sums: Record<string, number>; impressions: number }>();

  for (const r of records) {
    let entry = map.get(r.variantId);
    if (!entry) {
      entry = { sums: {}, impressions: 0 };
      map.set(r.variantId, entry);
    }
    entry.impressions += 1;
    for (const [k, v] of Object.entries(r.metrics)) {
      entry.sums[k] = (entry.sums[k] ?? 0) + v;
    }
  }

  return Array.from(map.entries()).map(([variantId, { sums, impressions }]) => ({
    variantId,
    impressions,
    sums,
    means: Object.fromEntries(
      Object.entries(sums).map(([k, v]) => [k, impressions > 0 ? v / impressions : 0])
    ),
  }));
}
