import type { Objective, ResolvedVariant, VariantStats } from "../types.js";

interface DecideOptions {
  variants: ResolvedVariant[];
  epsilon: number;
  stats: VariantStats[];
  objective: Objective;
  rng: () => number;
}

export function decide({ variants, epsilon, stats, objective, rng }: DecideOptions): string {
  if (variants.length === 0) throw new Error("decide: no variants");

  const pick = () => variants[Math.floor(rng() * variants.length)].id;

  if (rng() < epsilon) return pick();

  if (stats.length === 0) return pick();

  const statsMap = new Map(stats.map((s) => [s.variantId, s]));
  let bestId: string | null = null;
  let bestScore = -Infinity;
  let tied = false;

  for (const v of variants) {
    const s = statsMap.get(v.id);
    if (!s) continue;
    const score = objective(s);
    if (score > bestScore) {
      bestScore = score;
      bestId = v.id;
      tied = false;
    } else if (score === bestScore) {
      tied = true;
    }
  }

  if (bestId === null || tied) return pick();
  return bestId;
}
