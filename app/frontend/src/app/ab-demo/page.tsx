import { ABDemo } from "@/components/ABDemo";

export default function ABDemoPage() {
  return (
    <main style={{ padding: "2rem", maxWidth: "720px", margin: "0 auto" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "1.5rem" }}>
        auto-ab Demo
      </h1>
      <p style={{ color: "#666", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
        These components self-optimize via an epsilon-greedy bandit. Hover them to generate
        engagement, then reload — the winning variant is locked in a cookie for 24 h.
      </p>
      <ABDemo />
    </main>
  );
}
