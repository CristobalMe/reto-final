import React from "react";
import type { UseAutoABOptions } from "../../types.js";
import { useAutoAB } from "../useAutoAB.js";

interface ABPieChartProps extends UseAutoABOptions {
  experimentKey: string;
  data: { label: string; value: number }[];
  size?: number;
}

function arc(cx: number, cy: number, r: number, startAngle: number, endAngle: number): string {
  const start = {
    x: cx + r * Math.cos(startAngle),
    y: cy + r * Math.sin(startAngle),
  };
  const end = {
    x: cx + r * Math.cos(endAngle),
    y: cy + r * Math.sin(endAngle),
  };
  const large = endAngle - startAngle > Math.PI ? 1 : 0;
  return `M ${cx} ${cy} L ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y} Z`;
}

const PALETTE = ["#4f86f7", "#f74f4f", "#4ff77a", "#f7c44f", "#a44ff7", "#4ff7f0"];

export function ABPieChart({
  experimentKey,
  data,
  size: sizeProp = 150,
  ...options
}: ABPieChartProps) {
  const { resolved, containerProps } = useAutoAB(experimentKey, options);
  const cfg = resolved.config;

  const sz = cfg.size === "large" ? sizeProp * 1.3 : cfg.size === "small" ? sizeProp * 0.7 : sizeProp;
  const cx = sz / 2;
  const cy = sz / 2;
  const r = sz / 2 - 8;

  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  let angle = -Math.PI / 2;

  return (
    <div
      ref={containerProps.ref as React.RefCallback<HTMLDivElement>}
      style={containerProps.style}
      onPointerEnter={containerProps.onPointerEnter}
      onPointerLeave={containerProps.onPointerLeave}
      onPointerMove={containerProps.onPointerMove}
    >
      <svg width={sz} height={sz}>
        {data.map((d, i) => {
          const sweep = (d.value / total) * 2 * Math.PI;
          const pathD = arc(cx, cy, r, angle, angle + sweep);
          angle += sweep;
          const fill = cfg.color ? String(cfg.color) : PALETTE[i % PALETTE.length];
          return <path key={i} d={pathD} fill={fill} stroke="#fff" strokeWidth={1} />;
        })}
      </svg>
    </div>
  );
}
