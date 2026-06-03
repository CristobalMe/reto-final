// FNV-1a 32-bit hash
function fnv1a32(str: string): number {
  let hash = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash = (hash * 0x01000193) >>> 0;
  }
  return hash;
}

export function hashConfig(config: Record<string, string | number>): string {
  const sorted = Object.keys(config)
    .sort()
    .reduce<Record<string, string | number>>((acc, k) => {
      acc[k] = config[k];
      return acc;
    }, {});
  return fnv1a32(JSON.stringify(sorted)).toString(16).padStart(8, "0");
}

export function hashSeed(key: string): number {
  return fnv1a32(key);
}
