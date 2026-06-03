import type { Adapter, MetricsRecord } from "../types.js";
import { isBrowser } from "../core/env.js";

export class MetricsTracker {
  private hoverTimeMs = 0;
  private screenTimeMs = 0;
  private readonly sessionStart = Date.now();
  private customMetrics: Record<string, number> = {};

  private hoverStart: number | null = null;
  private lastMoveTs: number | null = null;
  private screenStart: number | null = null;

  private flushTimer: ReturnType<typeof setInterval> | null = null;
  private observer: IntersectionObserver | null = null;
  private pending: MetricsRecord[] = [];
  private destroyed = false;

  constructor(
    private readonly experimentKey: string,
    private readonly variantId: string,
    private readonly variantConfig: Record<string, string | number>,
    private readonly sessionId: string,
    private readonly adapter: Adapter,
    private readonly flushIntervalMs: number
  ) {
    if (isBrowser()) {
      this.flushTimer = setInterval(() => this.flush(), this.flushIntervalMs);
      document.addEventListener("visibilitychange", this.onVisibilityChange);
      window.addEventListener("pagehide", this.onPageHide);
    }
  }

  attachRef(el: Element | null): void {
    if (!isBrowser()) return;
    this.observer?.disconnect();
    if (!el) return;
    this.observer = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          this.screenStart = Date.now();
        } else if (this.screenStart !== null) {
          this.screenTimeMs += Date.now() - this.screenStart;
          this.screenStart = null;
        }
      }
    });
    this.observer.observe(el);
  }

  onPointerEnter = (): void => {
    this.hoverStart = Date.now();
    this.lastMoveTs = Date.now();
  };

  onPointerMove = (): void => {
    const now = Date.now();
    if (this.lastMoveTs !== null) {
      this.hoverTimeMs += now - this.lastMoveTs;
    }
    this.lastMoveTs = now;
  };

  onPointerLeave = (): void => {
    if (this.lastMoveTs !== null) {
      this.hoverTimeMs += Date.now() - this.lastMoveTs;
    }
    this.hoverStart = null;
    this.lastMoveTs = null;
  };

  bump(name: string, delta = 1): void {
    this.customMetrics[name] = (this.customMetrics[name] ?? 0) + delta;
  }

  private buildRecord(): MetricsRecord {
    const sessionTimeMs = Date.now() - this.sessionStart;
    const screenTime =
      this.screenStart !== null
        ? this.screenTimeMs + (Date.now() - this.screenStart)
        : this.screenTimeMs;
    return {
      experimentKey: this.experimentKey,
      variantId: this.variantId,
      variantConfig: this.variantConfig,
      sessionId: this.sessionId,
      metrics: {
        hoverTimeMs: this.hoverTimeMs,
        screenTimeMs: screenTime,
        sessionTimeMs,
        ...this.customMetrics,
      },
      timestamp: new Date().toISOString(),
    };
  }

  async flush(): Promise<void> {
    if (this.destroyed) return;
    const record = this.buildRecord();
    this.pending.push(record);
    const batch = [...this.pending];
    this.pending = [];
    try {
      await this.adapter.recordMetrics(batch);
    } catch {
      // best-effort: discard on error
    }
  }

  destroy(): void {
    this.destroyed = true;
    if (this.flushTimer !== null) clearInterval(this.flushTimer);
    this.observer?.disconnect();
    if (isBrowser()) {
      document.removeEventListener("visibilitychange", this.onVisibilityChange);
      window.removeEventListener("pagehide", this.onPageHide);
    }
    this.flush();
  }

  private onVisibilityChange = (): void => {
    if (document.visibilityState === "hidden") this.flush();
  };

  private onPageHide = (): void => {
    this.flush();
  };
}
