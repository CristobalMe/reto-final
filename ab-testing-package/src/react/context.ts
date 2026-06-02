import { createContext } from "react";
import type { ABProviderConfig } from "../types.js";
import { InMemoryAdapter } from "../adapters/memory.js";

export interface ABContextValue extends Required<ABProviderConfig> {}

const DEFAULT_TTL = 24 * 60 * 60 * 1000;

export const ABContext = createContext<ABContextValue>({
  adapter: new InMemoryAdapter(),
  defaultEpsilon: 0.2,
  decisionTTL: DEFAULT_TTL,
  cookieOptions: {},
  flushIntervalMs: 5000,
});
