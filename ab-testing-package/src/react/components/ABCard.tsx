import React from "react";
import type { UseAutoABOptions } from "../../types.js";
import { useAutoAB } from "../useAutoAB.js";

interface ABCardProps extends UseAutoABOptions {
  experimentKey: string;
  children: React.ReactNode;
}

const PADDING: Record<string, string> = {
  small: "8px",
  medium: "16px",
  large: "24px",
};

export function ABCard({ experimentKey, children, ...options }: ABCardProps) {
  const { resolved, containerProps } = useAutoAB(experimentKey, options);
  const cfg = resolved.config;

  const isRow = cfg.layout === "row";
  const padding = PADDING[String(cfg.size)] ?? "16px";
  const bg = cfg.color ? String(cfg.color) : "transparent";

  const style: React.CSSProperties = {
    ...containerProps.style,
    display: isRow ? "flex" : "block",
    flexDirection: isRow ? "row" : undefined,
    padding,
    backgroundColor: bg,
    borderRadius: "8px",
    boxSizing: "border-box",
  };

  return (
    <div
      ref={containerProps.ref as React.RefCallback<HTMLDivElement>}
      style={style}
      onPointerEnter={containerProps.onPointerEnter}
      onPointerLeave={containerProps.onPointerLeave}
      onPointerMove={containerProps.onPointerMove}
    >
      {children}
    </div>
  );
}
