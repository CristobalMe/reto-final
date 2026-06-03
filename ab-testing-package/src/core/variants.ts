import type { Dimensions, ResolvedVariant } from "../types.js";
import { resolveNumeric } from "./dimensions.js";
import { hashConfig, hashSeed } from "./hash.js";
import { mulberry32 } from "./rng.js";

function cartesian(lists: [string, (string | number)[]][]): Record<string, string | number>[] {
  if (lists.length === 0) return [{}];
  const [first, ...rest] = lists;
  const restCombos = cartesian(rest);
  return first[1].flatMap((val) =>
    restCombos.map((combo) => ({ [first[0]]: val, ...combo }))
  );
}

export function buildVariants(
  dimensions: Dimensions,
  experimentKey: string,
  maxVariants = 24
): ResolvedVariant[] {
  const entries: [string, (string | number)[]][] = [];
  if (dimensions.fontSize !== undefined)
    entries.push(["fontSize", resolveNumeric(dimensions.fontSize)]);
  if (dimensions.fontFamily !== undefined)
    entries.push(["fontFamily", dimensions.fontFamily]);
  if (dimensions.color !== undefined)
    entries.push(["color", dimensions.color]);
  if (dimensions.layout !== undefined)
    entries.push(["layout", dimensions.layout]);
  if (dimensions.size !== undefined)
    entries.push(["size", dimensions.size]);

  const all = cartesian(entries).map((config) => ({
    id: hashConfig(config),
    config,
  }));

  // stable sort by id so index-0 is deterministic (SSR default)
  all.sort((a, b) => a.id.localeCompare(b.id));

  if (all.length <= maxVariants) return all;

  // seeded shuffle-take
  const seed = hashSeed(experimentKey);
  const rng = mulberry32(seed);
  const copy = [...all];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  const sampled = copy.slice(0, maxVariants);
  sampled.sort((a, b) => a.id.localeCompare(b.id));
  return sampled;
}
