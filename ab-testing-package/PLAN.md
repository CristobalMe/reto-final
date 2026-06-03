# Plan: `auto-ab` — Self-Optimizing React Component Library

## Context

The Talos dashboard (`app/frontend`, Next.js 16 + React 19 + TS + Tailwind 4) currently
ships static UI. The goal is a **standalone, client-only React component library** at
`ab-testing-package/` that makes UI components self-optimizing via an **epsilon-greedy
multi-armed bandit**: components auto-generate visual variants from supplied ranges,
track engagement (hover/screen/session time), persist the chosen variant in a cookie,
and converge on the best performer. The package **never touches a DB** — it defines a
data schema + pluggable `Adapter` interface the consumer wires to their backend, and
ships in-memory + localStorage adapters for dev.

Decisions confirmed with user:
- **Package name:** `auto-ab` (matches `useAutoAB` hook + `autoab:` cookie prefix).
- **Styling:** neutral inline styles only — components apply the bandit-resolved
  dimensions; no baked-in theme. The example/demo supply their own CSS.
- **Scope:** build the standalone package + Vite example **and** wire a demo into the
  existing Talos Next.js app.

The existing app already hand-rolls SVG charts (`AlertDashboard.tsx`: DonutChart,
TrendChart) with **no charting/testing deps** — consistent with the spec's "hand-roll
SVG, no runtime deps" rule. We mirror that.

## Tooling (package)

- TS, React 18+ as the **only peer dependency**. No runtime deps.
- Build: **tsup** → ESM + CJS + `.d.ts`.
- Test: **Vitest + React Testing Library + jsdom**.
- Example: **Vite** app in `ab-testing-package/example/`.

## File structure

```
ab-testing-package/
  package.json  tsconfig.json  tsup.config.ts  vitest.config.ts  vitest.setup.ts
  README.md  PLAN.md  .gitignore
  src/
    index.ts                 # public API barrel
    types.ts                 # Dimensions, MetricsRecord, VariantStats, Adapter, configs
    core/
      hash.ts                # deterministic FNV-1a hash (variant ids + seeds)
      rng.ts                 # mulberry32 seeded PRNG + uniform()
      dimensions.ts          # resolve {min,max,step}|list -> value[] per dim
      variants.ts            # cartesian product, maxVariants seeded sampling, stable id
      objective.ts           # default score(stats) = mean hoverTimeMs; helpers
      epsilonGreedy.ts       # decide(variants, epsilon, stats, objective, rng)
      cookie.ts              # SSR-safe read/write `autoab:{key}` w/ attrs + TTL
      session.ts             # sessionStorage session id (generate if absent)
      env.ts                 # isBrowser() guards
    metrics/
      tracker.ts             # MetricsTracker: hover/screen/session accumulation + batched flush
    adapters/
      serialize.ts           # serializeRecord / parseStats
      memory.ts              # InMemoryAdapter
      localStorage.ts        # LocalStorageAdapter
    react/
      context.ts             # ABContext + defaults
      ABProvider.tsx
      useAutoAB.ts           # the hook (decision + tracker wiring)
      AutoAB.tsx             # generic render-prop / styled-box wrapper
      withAutoAB.tsx         # HOC
      components/
        ABText.tsx  ABCard.tsx  ABFilter.tsx
        ABLinePlot.tsx  ABBarPlot.tsx  ABPieChart.tsx
    __tests__/
      variants.test.ts  epsilonGreedy.test.ts  cookie.test.ts  metrics.test.tsx
  example/
    package.json  vite.config.ts  index.html
    src/main.tsx  src/App.tsx     # demos every component, in-memory adapter, visible convergence
```

## Module-by-module implementation

### 1. `types.ts` (contracts first)
- `NumericDimension = number[] | { min: number; max: number; step: number }`
- `EnumDimension<T> = T[]`
- `Dimensions` = optional `fontSize` (numeric), `fontFamily`/`color`/`layout`/`size` (enum).
  `layout`/`size` typed as `string` enums (component-specific values, one base schema).
- `ResolvedVariant = { id: string; config: Record<string, string|number> }`.
- `MetricsRecord = { experimentKey, variantId, variantConfig, sessionId,
  metrics: { hoverTimeMs, screenTimeMs, sessionTimeMs, [k:string]: number },
  timestamp: string /* ISO-8601 */ }`.
- `VariantStats = { variantId, impressions, means: Record<string, number>,
  sums: Record<string, number> }`.
- `Adapter = { recordMetrics(records: MetricsRecord[]): Promise<void>;
  fetchStats(experimentKey: string): Promise<VariantStats[]> }`.
- `Objective = (stats: VariantStats) => number`.
- `CookieOptions = { enabled?: boolean; sameSite?; path?; secure?; }` (expires derived from TTL).
- `ABProviderConfig = { adapter, defaultEpsilon?, decisionTTL?, cookieOptions?, flushIntervalMs? }`.

### 2. `core/` primitives (pure, fully unit-tested)
- `hash.ts`: FNV-1a over JSON.stringify(sortedConfig) → hex id; also a string→uint32 seed.
- `rng.ts`: `mulberry32(seed)` → `() => float in [0,1)`; injectable so tests can mock.
- `dimensions.ts`: expand each supplied dim to a concrete value list (numeric range →
  inclusive stepped list; lists pass through).
- `variants.ts`: cartesian product of resolved dims → variants; assign stable hash id;
  if `count > maxVariants` (default 24) deterministically sample using seed = hash(experimentKey)
  (shuffle-take), stable across reloads. Index-0 (stable-sorted) is the SSR default.
- `objective.ts`: `defaultObjective = s => s.means.hoverTimeMs ?? 0`; `byMetric(name)` helper.
- `epsilonGreedy.ts`: `decide({variants, epsilon, stats, objective, rng})` → variantId.
  `u = rng()`. `u < ε` → uniform random (EXPLORE). else argmax objective over stats
  (EXPLOIT); empty stats or tie → uniform random. Pure & deterministic given rng.
- `cookie.ts`: `readDecision(key)` / `writeDecision(key, {variantId, decidedAt, epsilon}, ttl, opts)`.
  SSR-guarded; respects `enabled === false` (no write). `expires` aligned to TTL.
- `session.ts`: `getSessionId()` from sessionStorage, generate (crypto.randomUUID fallback) if absent.
- `env.ts`: `isBrowser()`.

### 3. `metrics/tracker.ts`
- `MetricsTracker(experimentKey, variantId, variantConfig, sessionId, adapter, flushIntervalMs)`.
- Hover: `onPointerEnter` marks start; **`onPointerMove` accumulates `now - lastMoveTs`
  into hoverTimeMs and snapshots** (cheap: just arithmetic, no alloc per event);
  `onPointerLeave` finalizes.
- Screen: IntersectionObserver accumulates `screenTimeMs` while visible.
- Session: `sessionTimeMs = now - sessionStart`.
- Custom metrics map for the "etc." case (`bump(name, delta)`).
- Batched flush: debounced `flushIntervalMs` timer + on unmount + `visibilitychange`/
  `pagehide` → `adapter.recordMetrics([...])`. All listeners SSR-guarded.

### 4. `adapters/`
- `serialize.ts`: `serializeRecord` (→ DB-friendly JSON), `parseStats` (rows → VariantStats,
  computing means from sums/impressions).
- `memory.ts`: aggregates records in a Map; `fetchStats` returns computed means.
- `localStorage.ts`: same, persisted under a namespaced key; SSR-guarded.

### 5. `react/`
- `context.ts` + `ABProvider.tsx`: holds config (adapter, defaultEpsilon=0.2,
  decisionTTL=24h, cookieOptions, flushIntervalMs default ~5s).
- `useAutoAB(experimentKey, { dimensions, epsilon?, objective?, maxVariants? })`:
  1. Build variants (memoized). 2. **SSR/first render**: `pending=true`, `resolved` =
     variant index 0 (stable) → no hydration mismatch. 3. **Client effect**: read cookie;
     if fresh (`now-decidedAt < TTL`) reuse; else `fetchStats` + `decide` + write cookie
     (`decidedAt=now`), then set resolved + `pending=false`. 4. Instantiate MetricsTracker;
     return `containerProps = { ref, style, onPointerEnter, onPointerLeave, onPointerMove }`
     where `style` carries resolved dims; `ref` wires IntersectionObserver.
- `AutoAB.tsx`: render-prop (`children(resolved)`) or styled box spreading containerProps.
- `withAutoAB.tsx`: HOC injecting `resolved` + spreading containerProps.
- Components (neutral inline styles, map resolved dims → style/SVG attrs):
  - `ABText` (fontSize/fontFamily/color/size→weight), `ABCard` (layout/color/size/padding),
    `ABFilter` (dropdown when layout="dropdown", slider when "slider").
  - `ABLinePlot` / `ABBarPlot` / `ABPieChart`: **hand-rolled SVG** (own linear scale +
    arc math, mirroring `AlertDashboard.tsx`'s DonutChart approach), variant dims drive
    color/size/fontSize.

### 6. `index.ts`
Export hook, provider, components, AutoAB, withAutoAB, adapters, serializers, and all types.

## Talos app integration (`app/frontend`)
- Add local dep: `"auto-ab": "file:../../ab-testing-package"` to
  `app/frontend/package.json` (package built first via tsup so `dist/` exists).
- New client demo `app/frontend/src/components/ABDemo.tsx` (`'use client'`):
  wraps content in `<ABProvider>` with the in-memory (or localStorage) adapter and shows
  a couple of components (e.g. `ABCard` + `ABBarPlot`) self-optimizing.
- New route `app/frontend/src/app/ab-demo/page.tsx` rendering `<ABDemo/>`.
- Keep imports client-only; the provider/hook are `'use client'`. Verify no SSR hydration
  mismatch (pending → index-0 default covers this).

## Vite example (`ab-testing-package/example`)
Standalone Vite + React app demonstrating **every** component with the InMemoryAdapter,
with a control to fire synthetic engagement so the winner visibly converges (impressions
+ live argmax display).

## README
Document: install, `<ABProvider>` config, `useAutoAB` API, the data schema
(`MetricsRecord`/`VariantStats`), writing a real `Adapter` (incl. SQL row mapping via
`serializeRecord`/`parseStats`), epsilon-greedy behavior, cookie/TTL semantics, and the
**cookie-consent** degradation (`cookieOptions.enabled === false` → in-memory selection).

## Tests (Vitest, jsdom)
- `variants.test.ts`: cartesian product correctness; maxVariants seeded sampling is
  stable across runs; stable ids.
- `epsilonGreedy.test.ts`: mock rng → explore vs exploit branches; argmax; empty-stats &
  tie → uniform.
- `cookie.test.ts`: reuse within TTL (no re-roll) vs re-roll past TTL boundary;
  `enabled:false` writes nothing.
- `metrics.test.tsx`: pointermove accumulates hoverTimeMs; flush batches to adapter;
  mock cookies + IntersectionObserver in `vitest.setup.ts`.

## Build & order of work
1. Scaffold package (config files, empty src tree), confirm structure.
2. `types.ts` → `core/*` (+ tests) → `metrics/tracker.ts` → `adapters/*` →
   `react/*` (+ tests) → `index.ts`.
3. `npm run build` (tsup), `npm test` (vitest) green.
4. Vite example.
5. Wire Talos app demo route.

## Verification
- `cd ab-testing-package && npm install && npm test` → all suites pass.
- `npm run build` → `dist/` has ESM, CJS, `.d.ts`.
- `cd example && npm install && npm run dev` → open browser, trigger engagement,
  watch the winning variant converge (argmax stabilizes after exploration).
- Talos app: `cd app/frontend && npm install && npm run dev`, visit `/ab-demo`,
  confirm components render, reload does **not** re-roll the variant (cookie reuse),
  and no hydration warning in console.
