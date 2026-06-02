import React from "react";
import type { UseAutoABOptions } from "../../types.js";
import { useAutoAB } from "../useAutoAB.js";

interface ABTextProps extends UseAutoABOptions {
  experimentKey: string;
  children: React.ReactNode;
}

export function ABText({ experimentKey, children, ...options }: ABTextProps) {
  const { resolved, containerProps } = useAutoAB(experimentKey, options);
  const cfg = resolved.config;

  const style: React.CSSProperties = {
    ...containerProps.style,
    fontWeight: cfg.size === "large" ? 700 : cfg.size === "small" ? 400 : 500,
    display: "inline-block",
  };

  return (
    <span
      ref={containerProps.ref as React.RefCallback<HTMLSpanElement>}
      style={style}
      onPointerEnter={containerProps.onPointerEnter}
      onPointerLeave={containerProps.onPointerLeave}
      onPointerMove={containerProps.onPointerMove}
    >
      {children}
    </span>
  );
}
