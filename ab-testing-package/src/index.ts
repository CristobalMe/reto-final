// React
export { ABProvider } from "./react/ABProvider.js";
export { useAutoAB } from "./react/useAutoAB.js";
export { AutoAB } from "./react/AutoAB.js";
export { withAutoAB } from "./react/withAutoAB.js";
export { ABText } from "./react/components/ABText.js";
export { ABCard } from "./react/components/ABCard.js";
export { ABFilter } from "./react/components/ABFilter.js";
export { ABLinePlot } from "./react/components/ABLinePlot.js";
export { ABBarPlot } from "./react/components/ABBarPlot.js";
export { ABPieChart } from "./react/components/ABPieChart.js";

// Adapters
export { InMemoryAdapter } from "./adapters/memory.js";
export { LocalStorageAdapter } from "./adapters/localStorage.js";
export { serializeRecord, parseStats } from "./adapters/serialize.js";

// Core helpers
export { defaultObjective, byMetric } from "./core/objective.js";

// Types
export type {
  Dimensions,
  NumericDimension,
  EnumDimension,
  ResolvedVariant,
  MetricsRecord,
  VariantStats,
  Adapter,
  Objective,
  CookieOptions,
  ABProviderConfig,
  UseAutoABOptions,
  CookieDecision,
} from "./types.js";
