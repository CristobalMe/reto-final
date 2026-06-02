import { describe, it, expect, vi, beforeEach } from "vitest";
import { MetricsTracker } from "../metrics/tracker.js";
import type { Adapter, MetricsRecord } from "../types.js";

function makeAdapter(): Adapter & { records: MetricsRecord[][] } {
  const records: MetricsRecord[][] = [];
  return {
    records,
    async recordMetrics(batch) {
      records.push(batch);
    },
    async fetchStats() {
      return [];
    },
  };
}

beforeEach(() => {
  vi.useFakeTimers();
});

describe("MetricsTracker", () => {
  it("accumulates hoverTimeMs via onPointerMove", async () => {
    const adapter = makeAdapter();
    const tracker = new MetricsTracker("exp", "v1", {}, "s1", adapter, 100_000);

    tracker.onPointerEnter();
    vi.advanceTimersByTime(100);
    tracker.onPointerMove();
    vi.advanceTimersByTime(200);
    tracker.onPointerMove();
    vi.advanceTimersByTime(150);
    tracker.onPointerLeave();

    // hoverTimeMs ≈ 100+200+150 = 450ms (accumulated between moves)
    const record = (tracker as unknown as { buildRecord: () => MetricsRecord }).buildRecord?.();
    // flush and wait for the async adapter call to settle
    await tracker.flush();

    expect(adapter.records.length).toBeGreaterThan(0);
    const metric = adapter.records[0][0].metrics.hoverTimeMs;
    expect(metric).toBeGreaterThan(0);

    tracker.destroy();
  });

  it("flushes on interval", async () => {
    const adapter = makeAdapter();
    const tracker = new MetricsTracker("exp", "v1", {}, "s1", adapter, 500);

    vi.advanceTimersByTime(600);
    await Promise.resolve();

    expect(adapter.records.length).toBeGreaterThan(0);
    tracker.destroy();
  });

  it("flush sends correct experimentKey and variantId", async () => {
    const adapter = makeAdapter();
    const tracker = new MetricsTracker("my-exp", "variant-abc", { color: "red" }, "sess1", adapter, 100_000);

    await tracker.flush();

    expect(adapter.records[0][0].experimentKey).toBe("my-exp");
    expect(adapter.records[0][0].variantId).toBe("variant-abc");
    expect(adapter.records[0][0].variantConfig).toEqual({ color: "red" });

    tracker.destroy();
  });

  it("bump adds to custom metrics", async () => {
    const adapter = makeAdapter();
    const tracker = new MetricsTracker("exp", "v1", {}, "s1", adapter, 100_000);

    tracker.bump("clicks", 3);
    tracker.bump("clicks");

    await tracker.flush();

    expect(adapter.records[0][0].metrics.clicks).toBe(4);
    tracker.destroy();
  });
});
