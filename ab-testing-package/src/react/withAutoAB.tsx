import React from "react";
import type { ResolvedVariant, UseAutoABOptions } from "../types.js";
import { useAutoAB } from "./useAutoAB.js";

export interface WithAutoABProps {
  resolved: ResolvedVariant;
  pending: boolean;
}

export function withAutoAB<P extends WithAutoABProps>(
  WrappedComponent: React.ComponentType<P>,
  experimentKey: string,
  options: UseAutoABOptions
) {
  return function AutoABWrapper(props: Omit<P, keyof WithAutoABProps>) {
    const { resolved, pending, containerProps } = useAutoAB(experimentKey, options);
    return (
      <div {...containerProps}>
        <WrappedComponent
          {...(props as P)}
          resolved={resolved}
          pending={pending}
        />
      </div>
    );
  };
}
