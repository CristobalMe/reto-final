import { describe, it, expect, beforeEach } from "vitest";
import { readDecision, writeDecision } from "../core/cookie.js";

beforeEach(() => {
  // clear cookies
  document.cookie.split(";").forEach((c) => {
    const key = c.trim().split("=")[0];
    document.cookie = `${key}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
  });
});

describe("cookie", () => {
  it("reads back what was written", () => {
    const decision = { variantId: "abc123", decidedAt: Date.now(), epsilon: 0.2 };
    writeDecision("exp1", decision, 60_000);
    const result = readDecision("exp1");
    expect(result).not.toBeNull();
    expect(result?.variantId).toBe("abc123");
    expect(result?.epsilon).toBe(0.2);
  });

  it("returns null when no cookie exists", () => {
    expect(readDecision("nonexistent")).toBeNull();
  });

  it("does not write when enabled is false", () => {
    const decision = { variantId: "xyz", decidedAt: Date.now(), epsilon: 0.1 };
    writeDecision("exp2", decision, 60_000, { enabled: false });
    expect(readDecision("exp2")).toBeNull();
  });

  it("within TTL: same cookie is reusable", () => {
    const now = Date.now();
    const decision = { variantId: "v1", decidedAt: now, epsilon: 0.2 };
    writeDecision("exp3", decision, 60_000);
    const result = readDecision("exp3");
    expect(result?.decidedAt).toBe(now);
    expect(Date.now() - result!.decidedAt).toBeLessThan(60_000);
  });

  it("past TTL: old decidedAt indicates re-roll needed", () => {
    const old = Date.now() - 100_000; // 100 seconds ago
    const decision = { variantId: "v2", decidedAt: old, epsilon: 0.2 };
    writeDecision("exp4", decision, 200_000); // TTL not expired yet
    const result = readDecision("exp4");
    expect(result?.decidedAt).toBe(old);
    // consumer checks: Date.now() - decidedAt > TTL
    const TTL = 60_000;
    expect(Date.now() - result!.decidedAt).toBeGreaterThan(TTL);
  });
});
