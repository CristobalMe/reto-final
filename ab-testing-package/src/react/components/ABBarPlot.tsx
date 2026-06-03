import React from "react";
import type { UseAutoABOptions } from "../../types.js";
import { useAutoAB } from "../useAutoAB.js";

interface ABBarPlotProps extends UseAutoABOptions {
  experimentKey: string;
  data: { label: string; value: number }[];
  width?: number;
  height?: number;
}

export function ABBarPlot({
  experimentKey,
  data,
  width = 300,
  height = 150,
  ...options
}: ABBarPlotProps) {
  const { resolved, containerProps } = useAutoAB(experimentKey, options);
  const cfg = resolved.config;

  const color = cfg.color ? String(cfg.color) : "#4f86f7";
  const fontSize = cfg.fontSize ? Number(cfg.fontSize) : 11;

  const padTop = 8;
  const padBottom = 20;
  const padSide = 8;
  const chartH = height - padTop - padBottom;
  const chartW = width - padSide * 2;
  const max = Math.max(...data.map((d) => d.value), 1);
  const barW = Math.max(2, chartW / data.length - 4);

  return (
    <div
      ref={containerProps.ref as React.RefCallback<HTMLDivElement>}
      style={containerProps.style}
      onPointerEnter={containerProps.onPointerEnter}
      onPointerLeave={containerProps.onPointerLeave}
      onPointerMove={containerProps.onPointerMove}
    >
      <svg width={width} height={height}>
        {data.map((d, i) => {
          const barH = (d.value / max) * chartH;
          const x = padSide + i * (chartW / data.length) + (chartW / data.length - barW) / 2;
          const y = padTop + chartH - barH;
          return (
            <g key={i}>
              <rect x={x} y={y} width={barW} height={barH} fill={color} />
              <text
                x={x + barW / 2}
                y={height - 4}
                textAnchor="middle"
                fontSize={fontSize}
                fill={color}
              >
                {d.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
