import React from "react";
import type { UseAutoABOptions } from "../../types.js";
import { useAutoAB } from "../useAutoAB.js";

interface ABLinePlotProps extends UseAutoABOptions {
  experimentKey: string;
  data: number[];
  width?: number;
  height?: number;
  label?: string;
}

export function ABLinePlot({
  experimentKey,
  data,
  width = 300,
  height = 150,
  label,
  ...options
}: ABLinePlotProps) {
  const { resolved, containerProps } = useAutoAB(experimentKey, options);
  const cfg = resolved.config;

  const color = cfg.color ? String(cfg.color) : "#4f86f7";
  const fontSize = cfg.fontSize ? Number(cfg.fontSize) : 12;

  const pad = 24;
  const w = width - pad * 2;
  const h = height - pad * 2;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const scaleX = (i: number) => pad + (i / Math.max(data.length - 1, 1)) * w;
  const scaleY = (v: number) => pad + h - ((v - min) / range) * h;

  const points = data.map((v, i) => `${scaleX(i)},${scaleY(v)}`).join(" ");

  return (
    <div
      ref={containerProps.ref as React.RefCallback<HTMLDivElement>}
      style={containerProps.style}
      onPointerEnter={containerProps.onPointerEnter}
      onPointerLeave={containerProps.onPointerLeave}
      onPointerMove={containerProps.onPointerMove}
    >
      <svg width={width} height={height}>
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth={cfg.size === "large" ? 3 : cfg.size === "small" ? 1 : 2}
        />
        {data.map((v, i) => (
          <circle
            key={i}
            cx={scaleX(i)}
            cy={scaleY(v)}
            r={cfg.size === "large" ? 4 : 3}
            fill={color}
          />
        ))}
        {label && (
          <text x={pad} y={fontSize + 4} fontSize={fontSize} fill={color}>
            {label}
          </text>
        )}
      </svg>
    </div>
  );
}
