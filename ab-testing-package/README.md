# auto-ab

Paquete de A/B testing para React basado en epsilon-greedy multi-armed bandit. Cada experimento define dimensiones (fontSize, color, layout, etc.), genera variantes como el producto cartesiano de esas dimensiones, y elige la variante con mejor métrica de engagement usando el algoritmo epsilon-greedy. Las decisiones persisten en cookies por sesión.

## Instalación

```bash
# Desde el repo (el frontend ya lo consume así)
npm install ../ab-testing-package
```

## Uso básico

### 1. Envuelve tu app con `ABProvider`

```tsx
import { ABProvider, LocalStorageAdapter } from 'auto-ab';

const adapter = new LocalStorageAdapter('mi-app');

<ABProvider
  adapter={adapter}
  defaultEpsilon={0.15}   // 15% exploración, 85% explotación
  flushIntervalMs={4000}  // flushe métricas cada 4s
  cookieOptions={{ enabled: true }}
>
  <App />
</ABProvider>
```

### 2. Usa `useAutoAB` en cualquier componente

```tsx
import { useAutoAB } from 'auto-ab';

function MyButton() {
  const { resolved, containerProps } = useAutoAB('cta-button', {
    dimensions: {
      color: ['#2563eb', '#7c3aed', '#059669'],
      size: ['small', 'medium', 'large'],
    },
  });

  return (
    <button
      {...containerProps}  // adjunta el tracker de hover/screen time
      style={{ backgroundColor: String(resolved.config.color) }}
    >
      Comprar
    </button>
  );
}
```

`resolved.config` contiene los valores de cada dimensión para la variante asignada a esta sesión.

## Cómo funciona

### Variantes

`buildVariants(dimensions, experimentKey, maxVariants)` genera el producto cartesiano de todos los valores de cada dimensión y trunca a `maxVariants` (default 24). Cada variante tiene un `id` estable basado en su configuración y la clave del experimento.

### Decisión epsilon-greedy

En cada sesión nueva:

1. Se consulta `adapter.fetchStats(experimentKey)` para obtener las métricas acumuladas de cada variante.
2. Con probabilidad `epsilon`: elige una variante al azar (exploración).
3. Con probabilidad `1 - epsilon`: elige la variante con mejor puntuación según la función `objective` (explotación).
4. La decisión se escribe en una cookie con TTL de 24 horas, por lo que la misma sesión siempre ve la misma variante.

Si hay empate o no hay datos, se elige al azar.

### Función objective

Por defecto (`defaultObjective`) maximiza:

```
objective(stats) = 0.6 * normalizedHoverTime + 0.4 * normalizedScreenTime
```

Se puede pasar una función `objective` personalizada que recibe `VariantStats` y regresa un número.

### Métricas recolectadas

El `MetricsTracker` mide por variante y sesión:
- `hoverTimeMs` — tiempo acumulado con puntero dentro del contenedor
- `screenTimeMs` — tiempo que el contenedor estuvo visible en viewport
- `sessionTimeMs` — duración total de la sesión

Se flushean al adapter cada `flushIntervalMs` ms y también al hacer `destroy()`.

## API

### `<ABProvider>`

| Prop | Tipo | Default | Descripción |
|------|------|---------|-------------|
| `adapter` | `Adapter` | — | Dónde leer/escribir métricas |
| `defaultEpsilon` | `number` | `0.2` | Probabilidad de exploración (0–1) |
| `decisionTTL` | `number` | `86400000` | TTL de la cookie de decisión en ms |
| `cookieOptions` | `CookieOptions` | `{}` | `enabled`, `sameSite`, `path`, `secure` |
| `flushIntervalMs` | `number` | `5000` | Intervalo de flush de métricas en ms |

### `useAutoAB(experimentKey, options)`

| Opción | Tipo | Default | Descripción |
|--------|------|---------|-------------|
| `dimensions` | `Dimensions` | — | Dimensiones y sus posibles valores |
| `epsilon` | `number` | `defaultEpsilon` | Override por experimento |
| `objective` | `Objective` | `defaultObjective` | Función de scoring |
| `maxVariants` | `number` | `24` | Máximo de variantes a generar |

Regresa:

```ts
{
  resolved: ResolvedVariant;   // variante asignada ({ id, config })
  pending: boolean;            // true hasta que se resuelve la variante en cliente
  containerProps: {            // spread en el elemento a medir
    ref, style, onPointerEnter, onPointerLeave, onPointerMove
  }
}
```

`containerProps.style` aplica automáticamente `fontSize`, `fontFamily` y `color` si están en las dimensiones.

### Adapters

**`LocalStorageAdapter(namespace)`** — persiste métricas en localStorage del navegador. Útil para desarrollo y demos.

**`InMemoryAdapter`** — solo en memoria, se pierde al recargar. Útil para tests.

Para producción, implementa la interfaz `Adapter`:

```ts
interface Adapter {
  recordMetrics(records: MetricsRecord[]): Promise<void>;
  fetchStats(experimentKey: string): Promise<VariantStats[]>;
}
```

### Componentes de visualización

Todos aceptan un prop `experimentKey` y renderizan estadísticas de ese experimento:

- `ABCard` — resumen por variante en tarjetas
- `ABText` — texto con la variante activa
- `ABFilter` — chips de filtro con A/B en estilo
- `ABLinePlot` — serie de tiempo de métricas
- `ABBarPlot` — barras comparativas por variante
- `ABPieChart` — distribución de impresiones

### HOC `withAutoAB`

```tsx
const TrackedButton = withAutoAB(Button, 'cta-button', {
  dimensions: { color: ['#2563eb', '#7c3aed'] },
});
```

Inyecta `resolved` y `containerProps` como props al componente envuelto.

## Dimensiones disponibles

```ts
interface Dimensions {
  fontSize?:   number[] | { min: number; max: number; step: number };
  fontFamily?: string[];
  color?:      string[];
  layout?:     string[];
  size?:       string[];
}
```

## Tipos principales

```ts
type ResolvedVariant = {
  id: string;
  config: Record<string, string | number>;
};

type VariantStats = {
  variantId: string;
  impressions: number;
  means: Record<string, number>;
  sums: Record<string, number>;
};
```

## Desarrollo del paquete

```bash
cd ab-testing-package
npm install
npm run build      # genera dist/
npm test           # vitest
npm run dev        # build en watch mode
```

```bash
# Correr el ejemplo interactivo
cd ab-testing-package/example
npm install
npm run dev        # http://localhost:5173
```

## Opt-out

El dashboard de TALOS expone un botón "AB on/off" en el topbar. Cuando está desactivado, `ABProvider` recibe un adapter no-op que nunca guarda ni lee métricas, y `cookieOptions.enabled` se pone en `false`.

```tsx
const noopAdapter = {
  async recordMetrics() {},
  async fetchStats() { return []; },
};

<ABProvider adapter={abOptOut ? noopAdapter : realAdapter} cookieOptions={{ enabled: !abOptOut }}>
```
