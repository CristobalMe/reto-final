export type NumericDimension = number[] | { min: number; max: number; step: number };
export type EnumDimension<T extends string | number> = T[];

export interface Dimensions {
  fontSize?: NumericDimension;
  fontFamily?: EnumDimension<string>;
  color?: EnumDimension<string>;
  layout?: EnumDimension<string>;
  size?: EnumDimension<string>;
}

export interface ResolvedVariant {
  id: string;
  config: Record<string, string | number>;
}

export interface MetricsRecord {
  experimentKey: string;
  variantId: string;
  variantConfig: Record<string, string | number>;
  sessionId: string;
  metrics: {
    hoverTimeMs: number;
    screenTimeMs: number;
    sessionTimeMs: number;
    [k: string]: number;
  };
  timestamp: string;
}

export interface VariantStats {
  variantId: string;
  impressions: number;
  means: Record<string, number>;
  sums: Record<string, number>;
}

export interface Adapter {
  recordMetrics(records: MetricsRecord[]): Promise<void>;
  fetchStats(experimentKey: string): Promise<VariantStats[]>;
}

export type Objective = (stats: VariantStats) => number;

export interface CookieOptions {
  enabled?: boolean;
  sameSite?: "Strict" | "Lax" | "None";
  path?: string;
  secure?: boolean;
}

export interface ABProviderConfig {
  adapter: Adapter;
  defaultEpsilon?: number;
  decisionTTL?: number;
  cookieOptions?: CookieOptions;
  flushIntervalMs?: number;
}

export interface UseAutoABOptions {
  dimensions: Dimensions;
  epsilon?: number;
  objective?: Objective;
  maxVariants?: number;
}

export interface CookieDecision {
  variantId: string;
  decidedAt: number;
  epsilon: number;
}
