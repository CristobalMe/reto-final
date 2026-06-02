import React from "react";
import type { ABProviderConfig } from "../types.js";
import { ABContext } from "./context.js";

interface Props extends ABProviderConfig {
  children: React.ReactNode;
}

export function ABProvider({
  children,
  adapter,
  defaultEpsilon = 0.2,
  decisionTTL = 24 * 60 * 60 * 1000,
  cookieOptions = {},
  flushIntervalMs = 5000,
}: Props) {
  return (
    <ABContext.Provider
      value={{ adapter, defaultEpsilon, decisionTTL, cookieOptions, flushIntervalMs }}
    >
      {children}
    </ABContext.Provider>
  );
}
