import type { Objective, VariantStats } from "../types.js";

export const defaultObjective: Objective = (s: VariantStats) =>
  s.means.hoverTimeMs ?? 0;

export function byMetric(name: string): Objective {
  return (s: VariantStats) => s.means[name] ?? 0;
}
