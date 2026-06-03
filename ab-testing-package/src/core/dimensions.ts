import type { NumericDimension } from "../types.js";

export function resolveNumeric(dim: NumericDimension): number[] {
  if (Array.isArray(dim)) return dim;
  const { min, max, step } = dim;
  const values: number[] = [];
  for (let v = min; v <= max + Number.EPSILON; v += step) {
    values.push(Math.round(v * 1e9) / 1e9);
  }
  return values;
}
