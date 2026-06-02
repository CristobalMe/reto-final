import type { Adapter, MetricsRecord, VariantStats } from "../types.js";
import { isBrowser } from "../core/env.js";
import { parseStats } from "./serialize.js";

export class LocalStorageAdapter implements Adapter {
  constructor(private readonly namespace = "autoab") {}

  private key(experimentKey: string) {
    return `${this.namespace}:${experimentKey}`;
  }

  private load(experimentKey: string): MetricsRecord[] {
    if (!isBrowser()) return [];
    try {
      const raw = localStorage.getItem(this.key(experimentKey));
      return raw ? (JSON.parse(raw) as MetricsRecord[]) : [];
    } catch {
      return [];
    }
  }

  private save(experimentKey: string, records: MetricsRecord[]): void {
    if (!isBrowser()) return;
    try {
      localStorage.setItem(this.key(experimentKey), JSON.stringify(records));
    } catch {
      // quota exceeded — best effort
    }
  }

  async recordMetrics(incoming: MetricsRecord[]): Promise<void> {
    const byKey = new Map<string, MetricsRecord[]>();
    for (const r of incoming) {
      const list = byKey.get(r.experimentKey) ?? [];
      list.push(r);
      byKey.set(r.experimentKey, list);
    }
    for (const [key, newRecords] of byKey) {
      const existing = this.load(key);
      this.save(key, [...existing, ...newRecords]);
    }
  }

  async fetchStats(experimentKey: string): Promise<VariantStats[]> {
    return parseStats(this.load(experimentKey));
  }

  clear(experimentKey?: string): void {
    if (!isBrowser()) return;
    if (experimentKey) {
      localStorage.removeItem(this.key(experimentKey));
    } else {
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const k = localStorage.key(i);
        if (k?.startsWith(this.namespace + ":")) localStorage.removeItem(k);
      }
    }
  }
}
