import { describe, it, expect } from "vitest";
import { decide } from "../core/epsilonGreedy.js";
import { defaultObjective } from "../core/objective.js";
import type { ResolvedVariant, VariantStats } from "../types.js";

const variants: ResolvedVariant[] = [
  { id: "aaa", config: { color: "red" } },
  { id: "bbb", config: { color: "blue" } },
  { id: "ccc", config: { color: "green" } },
];

const statsWithWinner: VariantStats[] = [
  { variantId: "aaa", impressions: 10, sums: { hoverTimeMs: 100 }, means: { hoverTimeMs: 10 } },
  { variantId: "bbb", impressions: 10, sums: { hoverTimeMs: 500 }, means: { hoverTimeMs: 50 } },
  { variantId: "ccc", impressions: 10, sums: { hoverTimeMs: 200 }, means: { hoverTimeMs: 20 } },
];

describe("decide", () => {
  it("exploits when rng >= epsilon", () => {
    // rng always returns 0.5, epsilon = 0.2 → exploit → pick bbb (highest mean)
    const rng = (() => {
      let call = 0;
      return () => (call++ === 0 ? 0.5 : 0.5);
    })();
    const id = decide({ variants, epsilon: 0.2, stats: statsWithWinner, objective: defaultObjective, rng });
    expect(id).toBe("bbb");
  });

  it("explores when rng < epsilon", () => {
    // first call returns 0 (< epsilon) → explore
    let pickCall = 0;
    const rng = () => {
      if (pickCall++ === 0) return 0; // triggers explore
      return 0; // picks index 0
    };
    const id = decide({ variants, epsilon: 0.2, stats: statsWithWinner, objective: defaultObjective, rng });
    expect(variants.map((v) => v.id)).toContain(id);
  });

  it("returns a valid variant when stats is empty", () => {
    const rng = () => 0.9; // > epsilon, but no stats → random
    const id = decide({ variants, epsilon: 0.2, stats: [], objective: defaultObjective, rng });
    expect(variants.map((v) => v.id)).toContain(id);
  });

  it("returns a valid variant on tie", () => {
    const tiedStats: VariantStats[] = variants.map((v) => ({
      variantId: v.id,
      impressions: 5,
      sums: { hoverTimeMs: 50 },
      means: { hoverTimeMs: 10 },
    }));
    let call = 0;
    const rng = () => (call++ === 0 ? 0.9 : 0); // exploit path, tie → random pick
    const id = decide({ variants, epsilon: 0.1, stats: tiedStats, objective: defaultObjective, rng });
    expect(variants.map((v) => v.id)).toContain(id);
  });

  it("throws when variants is empty", () => {
    expect(() =>
      decide({ variants: [], epsilon: 0.2, stats: [], objective: defaultObjective, rng: Math.random })
    ).toThrow();
  });
});
