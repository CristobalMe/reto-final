import type { Adapter, MetricsRecord, VariantStats } from "../types.js";
import { parseStats } from "./serialize.js";

export class InMemoryAdapter implements Adapter {
  private records = new Map<string, MetricsRecord[]>();

  async recordMetrics(incoming: MetricsRecord[]): Promise<void> {
    for (const r of incoming) {
      const list = this.records.get(r.experimentKey) ?? [];
      list.push(r);
      this.records.set(r.experimentKey, list);
    }
  }

  async fetchStats(experimentKey: string): Promise<VariantStats[]> {
    return parseStats(this.records.get(experimentKey) ?? []);
  }

  clear(): void {
    this.records.clear();
  }
}
