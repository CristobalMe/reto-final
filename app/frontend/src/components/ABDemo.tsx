"use client";

import { ABProvider, ABCard, ABBarPlot, InMemoryAdapter } from "auto-ab";

const adapter = new InMemoryAdapter();

const BAR_DATA = [
  { label: "Mon", value: 12 },
  { label: "Tue", value: 28 },
  { label: "Wed", value: 19 },
  { label: "Thu", value: 35 },
  { label: "Fri", value: 22 },
];

export function ABDemo() {
  return (
    <ABProvider adapter={adapter} defaultEpsilon={0.2} flushIntervalMs={3000}>
      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        <ABCard
          experimentKey="talos-card"
          dimensions={{
            layout: ["row", "column"],
            color: ["#e8f4fd", "#fdf3e8", "#e8fdf0"],
            size: ["small", "medium", "large"],
          }}
        >
          <div style={{ padding: "8px", fontWeight: 600, fontSize: 16 }}>Self-Optimizing Card</div>
          <div style={{ padding: "8px", color: "#666" }}>
            Hover to generate engagement data. The bandit will converge on the best layout/color/size.
          </div>
        </ABCard>

        <ABBarPlot
          experimentKey="talos-bar"
          dimensions={{
            color: ["#4f86f7", "#a44ff7", "#f74f4f"],
            fontSize: [10, 12, 14],
          }}
          data={BAR_DATA}
          width={340}
          height={160}
        />
      </div>
    </ABProvider>
  );
}
