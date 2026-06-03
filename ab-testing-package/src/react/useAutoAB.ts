import { useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ResolvedVariant, UseAutoABOptions } from "../types.js";
import { buildVariants } from "../core/variants.js";
import { defaultObjective } from "../core/objective.js";
import { decide } from "../core/epsilonGreedy.js";
import { mulberry32 } from "../core/rng.js";
import { hashSeed } from "../core/hash.js";
import { readDecision, writeDecision } from "../core/cookie.js";
import { getSessionId } from "../core/session.js";
import { MetricsTracker } from "../metrics/tracker.js";
import { ABContext } from "./context.js";

export interface UseAutoABResult {
  resolved: ResolvedVariant;
  pending: boolean;
  containerProps: {
    ref: (el: HTMLElement | null) => void;
    style: React.CSSProperties;
    onPointerEnter: () => void;
    onPointerLeave: () => void;
    onPointerMove: () => void;
  };
}

export function useAutoAB(experimentKey: string, options: UseAutoABOptions): UseAutoABResult {
  const { adapter, defaultEpsilon, decisionTTL, cookieOptions, flushIntervalMs } =
    useContext(ABContext);

  const epsilon = options.epsilon ?? defaultEpsilon;
  const objective = options.objective ?? defaultObjective;
  const maxVariants = options.maxVariants ?? 24;

  const variants = useMemo(
    () => buildVariants(options.dimensions, experimentKey, maxVariants),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [experimentKey, maxVariants, JSON.stringify(options.dimensions)]
  );

  const [resolved, setResolved] = useState<ResolvedVariant>(variants[0]);
  const [pending, setPending] = useState(true);

  const trackerRef = useRef<MetricsTracker | null>(null);
  const sessionId = useMemo(() => getSessionId(), []);

  // resolve variant on client
  useEffect(() => {
    let cancelled = false;

    async function resolveVariant() {
      const cached = readDecision(experimentKey);
      if (cached && Date.now() - cached.decidedAt < decisionTTL) {
        const match = variants.find((v) => v.id === cached.variantId);
        if (match && !cancelled) {
          setResolved(match);
          setPending(false);
          return;
        }
      }

      const stats = await adapter.fetchStats(experimentKey);
      if (cancelled) return;

      const rng = mulberry32(hashSeed(experimentKey + Date.now()));
      const variantId = decide({ variants, epsilon, stats, objective, rng });
      const match = variants.find((v) => v.id === variantId) ?? variants[0];

      writeDecision(experimentKey, { variantId: match.id, decidedAt: Date.now(), epsilon }, decisionTTL, cookieOptions);

      if (!cancelled) {
        setResolved(match);
        setPending(false);
      }
    }

    resolveVariant();
    return () => { cancelled = true; };
  }, [experimentKey, adapter, decisionTTL, epsilon, cookieOptions, variants, objective]);

  // build tracker when resolved variant is known
  useEffect(() => {
    if (pending) return;
    trackerRef.current?.destroy();
    trackerRef.current = new MetricsTracker(
      experimentKey,
      resolved.id,
      resolved.config,
      sessionId,
      adapter,
      flushIntervalMs
    );
    return () => {
      trackerRef.current?.destroy();
      trackerRef.current = null;
    };
  }, [experimentKey, resolved.id, sessionId, adapter, flushIntervalMs, pending]);

  const refCallback = useCallback((el: HTMLElement | null) => {
    trackerRef.current?.attachRef(el);
  }, []);

  const style: React.CSSProperties = {};
  const cfg = resolved.config;
  if (cfg.fontSize !== undefined) style.fontSize = `${cfg.fontSize}px`;
  if (cfg.fontFamily !== undefined) style.fontFamily = String(cfg.fontFamily);
  if (cfg.color !== undefined) style.color = String(cfg.color);

  return {
    resolved,
    pending,
    containerProps: {
      ref: refCallback,
      style,
      onPointerEnter: () => trackerRef.current?.onPointerEnter(),
      onPointerLeave: () => trackerRef.current?.onPointerLeave(),
      onPointerMove: () => trackerRef.current?.onPointerMove(),
    },
  };
}
