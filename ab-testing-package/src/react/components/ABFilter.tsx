import React, { useState } from "react";
import type { UseAutoABOptions } from "../../types.js";
import { useAutoAB } from "../useAutoAB.js";

interface ABFilterProps extends UseAutoABOptions {
  experimentKey: string;
  options: string[];
  value?: string;
  onChange?: (val: string) => void;
  min?: number;
  max?: number;
}

export function ABFilter({
  experimentKey,
  options: filterOptions,
  value,
  onChange,
  min = 0,
  max = 100,
  ...abOptions
}: ABFilterProps) {
  const { resolved, containerProps } = useAutoAB(experimentKey, abOptions);
  const cfg = resolved.config;
  const isSlider = cfg.layout === "slider";

  const [internal, setInternal] = useState(value ?? (isSlider ? String(min) : filterOptions[0] ?? ""));

  const handleChange = (v: string) => {
    setInternal(v);
    onChange?.(v);
  };

  const style: React.CSSProperties = { ...containerProps.style };

  return (
    <div
      ref={containerProps.ref as React.RefCallback<HTMLDivElement>}
      onPointerEnter={containerProps.onPointerEnter}
      onPointerLeave={containerProps.onPointerLeave}
      onPointerMove={containerProps.onPointerMove}
    >
      {isSlider ? (
        <input
          type="range"
          min={min}
          max={max}
          value={internal}
          onChange={(e) => handleChange(e.target.value)}
          style={style}
        />
      ) : (
        <select
          value={internal}
          onChange={(e) => handleChange(e.target.value)}
          style={style}
        >
          {filterOptions.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      )}
    </div>
  );
}
