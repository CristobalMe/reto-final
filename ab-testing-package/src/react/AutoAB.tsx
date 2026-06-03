import React from "react";
import type { ResolvedVariant, UseAutoABOptions } from "../types.js";
import { useAutoAB } from "./useAutoAB.js";

interface AutoABProps extends UseAutoABOptions {
  experimentKey: string;
  children: (resolved: ResolvedVariant) => React.ReactNode;
  className?: string;
}

export function AutoAB({ experimentKey, children, className, ...options }: AutoABProps) {
  const { resolved, containerProps } = useAutoAB(experimentKey, options);
  return (
    <div {...containerProps} className={className}>
      {children(resolved)}
    </div>
  );
}
