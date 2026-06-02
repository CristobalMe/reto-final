import { describe, it, expect } from "vitest";
import { buildVariants } from "../core/variants.js";

describe("buildVariants", () => {
  it("returns cartesian product of dimensions", () => {
    const variants = buildVariants(
      { color: ["red", "blue"], size: ["small", "large"] },
      "test-exp"
    );
    expect(variants).toHaveLength(4);
    const configs = variants.map((v) => v.config);
    expect(configs).toContainEqual({ color: "red", size: "small" });
    expect(configs).toContainEqual({ color: "blue", size: "large" });
  });

  it("assigns stable hash ids", () => {
    const a = buildVariants({ color: ["red", "blue"] }, "exp1");
    const b = buildVariants({ color: ["red", "blue"] }, "exp1");
    expect(a.map((v) => v.id)).toEqual(b.map((v) => v.id));
  });

  it("samples down to maxVariants deterministically", () => {
    const dims = {
      color: ["r", "g", "b", "y"],
      size: ["s", "m", "l"],
      layout: ["a", "b", "c"],
    };
    const variants = buildVariants(dims, "big-exp", 10);
    expect(variants.length).toBe(10);

    const again = buildVariants(dims, "big-exp", 10);
    expect(variants.map((v) => v.id)).toEqual(again.map((v) => v.id));
  });

  it("sampled variants are stable-sorted by id", () => {
    const dims = { color: ["a", "b", "c", "d"], size: ["1", "2", "3"] };
    const variants = buildVariants(dims, "sort-test", 5);
    const ids = variants.map((v) => v.id);
    expect(ids).toEqual([...ids].sort());
  });

  it("index-0 is always the same SSR default", () => {
    const v1 = buildVariants({ color: ["red", "blue"] }, "exp");
    const v2 = buildVariants({ color: ["red", "blue"] }, "exp");
    expect(v1[0].id).toBe(v2[0].id);
  });

  it("resolves numeric range dimensions", () => {
    const variants = buildVariants(
      { fontSize: { min: 12, max: 16, step: 2 } },
      "font-exp"
    );
    const sizes = variants.map((v) => v.config.fontSize);
    expect(sizes).toContain(12);
    expect(sizes).toContain(14);
    expect(sizes).toContain(16);
  });
});
