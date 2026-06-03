import React, { useState } from "react";
import {
  ABProvider,
  InMemoryAdapter,
  ABText,
  ABCard,
  ABBarPlot,
  ABLinePlot,
  ABPieChart,
  ABFilter,
} from "auto-ab";

const adapter = new InMemoryAdapter();

const LINE_DATA = [4, 7, 2, 9, 5, 11, 8, 3, 10, 6];
const BAR_DATA = [
  { label: "A", value: 40 },
  { label: "B", value: 70 },
  { label: "C", value: 55 },
  { label: "D", value: 90 },
];
const PIE_DATA = [
  { label: "X", value: 30 },
  { label: "Y", value: 50 },
  { label: "Z", value: 20 },
];

function ConvergencePanel() {
  const [stats, setStats] = useState<{ variantId: string; hover: number }[]>([]);

  const refresh = async () => {
    const s = await adapter.fetchStats("card-layout");
    setStats(
      s
        .map((x) => ({ variantId: x.variantId.slice(0, 6), hover: Math.round(x.means.hoverTimeMs ?? 0) }))
        .sort((a, b) => b.hover - a.hover)
    );
  };

  return (
    <div className="section" style={{ background: "white", borderRadius: 8, padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
      <h2 style={{ fontSize: "1rem", color: "#555", marginTop: 0 }}>Live Convergence (card-layout experiment)</h2>
      <button onClick={refresh}>Refresh stats</button>
      {stats.length > 0 && (
        <pre style={{ fontSize: "0.8rem", color: "#555", marginTop: "0.5rem" }}>
          {stats.map((s) => `${s.variantId}: ${s.hover}ms avg hover`).join("\n")}
        </pre>
      )}
      {stats.length === 0 && <p style={{ fontSize: "0.8rem", color: "#aaa" }}>Hover the card below, then click Refresh.</p>}
    </div>
  );
}

function FilterDemo() {
  const [val, setVal] = useState<string>("Option A");
  return (
    <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
      <ABFilter
        experimentKey="filter-type"
        dimensions={{ layout: ["dropdown", "slider"] }}
        options={["Option A", "Option B", "Option C"]}
        value={val}
        onChange={setVal}
        min={0}
        max={100}
      />
      <span style={{ fontSize: "0.85rem", color: "#666" }}>value: {val}</span>
    </div>
  );
}

export default function App() {
  return (
    <ABProvider adapter={adapter} defaultEpsilon={0.3} decisionTTL={30_000} flushIntervalMs={2000}>
      <h1>auto-ab example — self-optimizing components</h1>

      <ConvergencePanel />

      <div style={{ background: "white", borderRadius: 8, padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
        <h2 style={{ fontSize: "1rem", color: "#555", marginTop: 0 }}>ABText — font size + family</h2>
        <ABText
          experimentKey="headline-font"
          dimensions={{ fontSize: { min: 14, max: 24, step: 4 }, fontFamily: ["sans-serif", "Georgia", "monospace"] }}
        >
          This text self-optimizes its font size and family
        </ABText>
      </div>

      <div style={{ background: "white", borderRadius: 8, padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
        <h2 style={{ fontSize: "1rem", color: "#555", marginTop: 0 }}>ABCard — layout + color + size</h2>
        <ABCard
          experimentKey="card-layout"
          dimensions={{
            layout: ["row", "column"],
            color: ["#e8f4fd", "#fdf3e8", "#e8fdf0"],
            size: ["small", "medium", "large"],
          }}
        >
          <div style={{ padding: "4px 8px", fontWeight: 600 }}>Card Title</div>
          <div style={{ padding: "4px 8px", color: "#666" }}>Hover me to generate engagement data</div>
        </ABCard>
      </div>

      <div style={{ background: "white", borderRadius: 8, padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
        <h2 style={{ fontSize: "1rem", color: "#555", marginTop: 0 }}>ABFilter — dropdown vs slider</h2>
        <FilterDemo />
      </div>

      <div style={{ background: "white", borderRadius: 8, padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
        <h2 style={{ fontSize: "1rem", color: "#555", marginTop: 0 }}>ABLinePlot — color + size</h2>
        <ABLinePlot
          experimentKey="line-chart"
          dimensions={{ color: ["#4f86f7", "#f74f4f", "#4ff77a"], size: ["small", "medium", "large"] }}
          data={LINE_DATA}
          label="Trend"
        />
      </div>

      <div style={{ background: "white", borderRadius: 8, padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
        <h2 style={{ fontSize: "1rem", color: "#555", marginTop: 0 }}>ABBarPlot — color + font size</h2>
        <ABBarPlot
          experimentKey="bar-chart"
          dimensions={{ color: ["#a44ff7", "#f7c44f", "#4ff7f0"], fontSize: [10, 12, 14] }}
          data={BAR_DATA}
        />
      </div>

      <div style={{ background: "white", borderRadius: 8, padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
        <h2 style={{ fontSize: "1rem", color: "#555", marginTop: 0 }}>ABPieChart — size</h2>
        <ABPieChart
          experimentKey="pie-chart"
          dimensions={{ size: ["small", "medium", "large"] }}
          data={PIE_DATA}
        />
      </div>
    </ABProvider>
  );
}
