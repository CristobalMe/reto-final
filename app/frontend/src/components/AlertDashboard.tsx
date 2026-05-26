'use client';

import Image from 'next/image';
import { useState, useMemo, useEffect, useCallback, useRef } from 'react';

const PULPO_JOKES = [
  '¿Por qué el pulpo es el mejor auditor? ¡Tiene ocho brazos para revisar ocho almacenes al mismo tiempo!',
  'El pulpo encontró un faltante de calamares. Obvio… se los comió él.',
  '¿Qué le dijo el pulpo al inventario? "Contigo tengo todo bien agarrado."',
  'Un pulpo en una auditoría es imparable: firma, revisa, sella, calcula, apunta, archiva, reporta… ¡y todavía le sobra un tentáculo!',
  '¿Por qué el pulpo no usa Excel? Porque con ocho manos prefiere ocho hojas de cálculo.',
  'El pulpo dice: "Yo no tengo discrepancias… solo tentáculos con criterio propio."',
  '¿Sabes por qué el pulpo es bueno en TALOS? Detecta anomalías con todos sus sentidos… ¡y son muchos!',
  '¿Por qué el pulpo nunca pierde la cuenta? Porque tiene ocho dedos y ningún jefe.',
  'El pulpo intentó hacer home office. Falló: necesitaba ocho monitores y solo tenía uno.',
  '¿Qué hace el pulpo cuando hay sobrante? Lo abraza con los ocho tentáculos y dice: "Este ya es mío."',
  '¿Cómo saluda el pulpo? "¡Hola, hola, hola, hola, hola, hola, hola, hola!"',
  'El pulpo pidió aumento. El jefe dijo que no. El pulpo apretó el botón de renuncia… ocho veces.',
];

// ─── Pulpo Mascot (green-screen chroma key via canvas) ────────────────────────
function PulpoMascot() {
  const videoRef  = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const walkerRef = useRef<HTMLDivElement>(null);
  const wrapRef   = useRef<HTMLDivElement>(null);
  const bubbleRef = useRef<HTMLDivElement>(null);
  const rafRef    = useRef<number>(0);
  const timerRef  = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pausedRef = useRef(false);
  const [joke, setJoke] = useState<string | null>(null);

  useEffect(() => { pausedRef.current = !!joke; }, [joke]);

  function handleClick() {
    if (timerRef.current) clearTimeout(timerRef.current);
    const next = PULPO_JOKES[Math.floor(Math.random() * PULPO_JOKES.length)];
    setJoke(next);
    timerRef.current = setTimeout(() => setJoke(null), 5000);
  }

  useEffect(() => {
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    const walker = walkerRef.current;
    const wrap   = wrapRef.current;
    if (!video || !canvas || !walker || !wrap) return;

    canvas.width  = 0;
    canvas.height = 0;

    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;

    const SPEED = 60;
    let x = 0;
    let dir = 1;
    let prev = 0;

    function tick(ts: number) {
      const dt = prev ? Math.min((ts - prev) / 1000, 0.1) : 0;
      prev = ts;

      const canvasW = canvas!.offsetWidth || 0;
      const travel  = Math.max(0, wrap!.offsetWidth - canvasW);

      if (!pausedRef.current) {
        x += dir * SPEED * dt;
        if (x >= travel) { x = travel; dir = -1; }
        if (x <= 0)      { x = 0;      dir =  1; }
        walker!.style.transform = `translateX(${x}px) scaleX(${dir === -1 ? -1 : 1})`;
      }

      // Clamp bubble horizontally so it never leaves the container
      const bubble = bubbleRef.current;
      if (bubble) {
        const bw      = bubble.offsetWidth || 210;
        const center  = x + canvasW / 2;
        const clamped = Math.max(bw / 2, Math.min(wrap!.offsetWidth - bw / 2, center));
        bubble.style.left      = `${clamped}px`;
        bubble.style.transform = 'translateX(-50%)';
      }

      // Chroma-key frame
      if (!video!.paused && !video!.ended && canvas!.width > 0) {
        ctx!.clearRect(0, 0, canvas!.width, canvas!.height);
        ctx!.drawImage(video!, 0, 0, canvas!.width, canvas!.height);
        const frame = ctx!.getImageData(0, 0, canvas!.width, canvas!.height);
        const d = frame.data;
        for (let i = 0; i < d.length; i += 4) {
          const r = d[i], g = d[i + 1], b = d[i + 2];
          if (g > 90 && g > r * 1.35 && g > b * 1.35) d[i + 3] = 0;
        }
        ctx!.putImageData(frame, 0, 0);
      }

      rafRef.current = requestAnimationFrame(tick);
    }

    function onMeta() {
      canvas!.width  = video!.videoWidth  || 320;
      canvas!.height = video!.videoHeight || 240;
    }

    video.addEventListener('loadedmetadata', onMeta);
    video.play().catch(() => {});
    rafRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafRef.current);
      video.removeEventListener('loadedmetadata', onMeta);
    };
  }, []);

  return (
    <div className="pulpo-mascot" ref={wrapRef}>
      <video ref={videoRef} src="/pulpo.mp4" loop muted playsInline style={{ display: 'none' }} />
      <div
        className="pulpo-walker"
        ref={walkerRef}
        onClick={handleClick}
        style={{ cursor: 'pointer', pointerEvents: 'auto' }}
      >
        <canvas ref={canvasRef} className="pulpo-canvas" />
      </div>
      {joke && (
        <div className="pulpo-bubble" ref={bubbleRef}>{joke}</div>
      )}
    </div>
  );
}
import type { DashboardAlert, AlertTipo, ClosureListItem, Severity } from '../lib/types';
import { fmtMoney, fmtNum, fmtDate } from '../lib/format';
import { listRecentClosures, getLocalReport } from '../lib/api';
import { mapFindings } from '../lib/mapFindings';

type FilterTipo = AlertTipo | 'all' | 'resolved';
type FilterSeverity = Severity | 'all';
type FilterCategory = string | 'all';
type SortBy = 'score' | 'mxn' | 'diff';

const TIPO_LABEL: Record<AlertTipo | 'resolved', string> = {
  loss: 'Faltantes',
  surplus: 'Sobrantes',
  missing: 'No contabilizados',
  resolved: 'Revisadas',
};

const SEV_ORDER: Record<Severity, number> = { CRITICA: 4, ALTA: 3, MEDIA: 2, BAJA: 1 };

// ─── Donut ────────────────────────────────────────────────────────────────────
function DonutChart({ alerts, revisadas }: { alerts: DashboardAlert[]; revisadas: Set<string> }) {
  const unresolved = alerts.filter(a => !revisadas.has(a.id));
  const counts = {
    loss: unresolved.filter(a => a.tipo === 'loss').length,
    surplus: unresolved.filter(a => a.tipo === 'surplus').length,
    missing: unresolved.filter(a => a.tipo === 'missing').length,
  };
  const total = counts.loss + counts.surplus + counts.missing;
  const size = 180;
  const stroke = 24;
  // Keep the stroke fully inside the SVG bounds to avoid clipping the ring edges.
  const r = (size - stroke) / 2, cx = size / 2, cy = size / 2;
  const circ = 2 * Math.PI * r;
  const segments = [
    { key: 'loss', count: counts.loss, color: 'var(--danger)' },
    { key: 'surplus', count: counts.surplus, color: 'var(--amber)' },
    { key: 'missing', count: counts.missing, color: 'var(--slate)' },
  ].filter(s => s.count > 0);
  let acc = 0;

  return (
    <div className="donut-wrap">
      <svg className="donut-svg" width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--muted-2)" strokeWidth={stroke} />
        {total > 0 && segments.map(s => {
          const len = (s.count / total) * circ;
          const el = (
            <circle
              key={s.key}
              cx={cx} cy={cy} r={r}
              fill="none"
              stroke={s.color}
              strokeWidth={stroke}
              strokeDasharray={`${len} ${circ}`}
              strokeDashoffset={-acc}
            />
          );
          acc += len;
          return el;
        })}
      </svg>
      <div className="donut-center">
        <span className="donut-count">{total}</span>
        <span className="donut-label">alertas</span>
      </div>
    </div>
  );
}

// ─── Severity tag ─────────────────────────────────────────────────────────────
function SevTag({ sev, isResolved }: { sev: Severity; isResolved: boolean }) {
  if (isResolved) return <span className="tag resolved">Revisada</span>;
  if (sev === 'CRITICA') return <span className="tag loss">CRÍTICA</span>;
  if (sev === 'ALTA') return <span className="tag loss">ALTA</span>;
  if (sev === 'MEDIA') return <span className="tag surplus">MEDIA</span>;
  return <span className="tag missing">BAJA</span>;
}

// ─── Tipo tag ─────────────────────────────────────────────────────────────────
function TipoTag({ tipo, isResolved }: { tipo: AlertTipo; isResolved: boolean }) {
  if (isResolved) return <span className="tag resolved">OK</span>;
  if (tipo === 'loss') return <span className="tag loss">Faltante</span>;
  if (tipo === 'surplus') return <span className="tag surplus">Sobrante</span>;
  return <span className="tag missing">No cont.</span>;
}

// ─── Trend Chart ──────────────────────────────────────────────────────────────
function TrendChart({ alerts, selectedId }: { alerts: DashboardAlert[]; selectedId: string | null }) {
  const top12 = useMemo(() => (
    [...alerts]
      .sort((a, b) => Math.abs(b.difimporte) - Math.abs(a.difimporte))
      .slice(0, 12)
  ), [alerts]);

  const maxVal = top12.reduce((m, a) => Math.max(m, Math.abs(a.difimporte)), 1);

  if (top12.length === 0) return null;

  return (
    <div className="trend-card">
      <p className="card-title">Impacto por producto · top 12</p>
      <div className="trend-chart">
        {top12.map(a => {
          const pct = Math.max(4, (Math.abs(a.difimporte) / maxVal) * 100);
          const isDanger = a.tipo === 'loss';
          const isSel = a.id === selectedId;
          return (
            <div
              key={a.id}
              className={`trend-bar${isDanger ? ' danger' : ''}`}
              style={{ height: `${pct}%`, opacity: isSel ? 1 : 0.7, outline: isSel ? '2px solid var(--ink-900)' : 'none', outlineOffset: '2px' }}
              title={`${a.producto_nombre}: ${fmtMoney(a.difimporte)}`}
            />
          );
        })}
      </div>
      <div className="trend-axis">
        <span>{top12[0]?.producto_nombre.slice(0, 14)}</span>
        <span>{top12[top12.length - 1]?.producto_nombre.slice(0, 14)}</span>
      </div>
    </div>
  );
}

// ─── Activity Feed ────────────────────────────────────────────────────────────
function ActivityFeed({ alerts }: { alerts: DashboardAlert[] }) {
  const top5 = useMemo(() => (
    [...alerts].sort((a, b) => b.score - a.score).slice(0, 5)
  ), [alerts]);

  return (
    <div className="card">
      <p className="card-title">Hallazgos más críticos</p>
      <div className="activity">
        {top5.map(a => (
          <div key={a.id} className="activity-row">
            <div className={`activity-dot${a.tipo === 'loss' ? ' danger' : a.tipo === 'surplus' ? ' amber' : ''}`} />
            <div className="activity-main">
              <p className="activity-text">{a.message}</p>
              <p className="activity-time mono">{a.producto_nombre} · score {a.score.toFixed(1)}</p>
            </div>
          </div>
        ))}
        {top5.length === 0 && <p style={{ color: 'var(--ink-500)', fontSize: 13 }}>Sin hallazgos</p>}
      </div>
    </div>
  );
}

// ─── Detail Panel ─────────────────────────────────────────────────────────────
function DetailPanel({
  alert,
  isResolved,
  onMarkRevisada,
  onReopen,
}: {
  alert: DashboardAlert;
  isResolved: boolean;
  onMarkRevisada: () => void;
  onReopen: () => void;
}) {
  const fisicoPct = alert.stockteorico > 0
    ? Math.min(100, (alert.stockfisico / alert.stockteorico) * 100)
    : 0;

  return (
    <div className="detail-card">
      <div className="detail-head">
        <div className="detail-kicker">
          <span className="tag" style={{ background: 'var(--olive-100)', color: 'var(--olive-700)' }}>
            {alert.metric_id}
          </span>
          <TipoTag tipo={alert.tipo} isResolved={isResolved} />
          <SevTag sev={alert.severity_label} isResolved={isResolved} />
        </div>
        <p className="detail-product">{alert.producto_nombre}</p>
        <p className="detail-sku">ID #{alert.idproducto ?? '—'} · {alert.producto_cat_nombre} · {alert.producto_unidad}</p>
      </div>

      <div className="detail-stat-grid">
        <div>
          <p className="detail-stat-lbl">Diferencia</p>
          <p className={`detail-stat-val big${alert.diferencia < 0 ? ' neg' : alert.diferencia > 0 ? ' pos' : ''}`}>
            {fmtNum(alert.diferencia, alert.producto_unidad !== '—' ? alert.producto_unidad : null)}
          </p>
        </div>
        <div>
          <p className="detail-stat-lbl">Impacto MXN</p>
          <p className={`detail-stat-val big${alert.difimporte < 0 ? ' neg' : alert.difimporte > 0 ? ' pos' : ''}`}>
            {fmtMoney(alert.difimporte)}
          </p>
        </div>
        <div>
          <p className="detail-stat-lbl">Stock teórico</p>
          <p className="detail-stat-val">{fmtNum(alert.stockteorico)}</p>
        </div>
        <div>
          <p className="detail-stat-lbl">Stock físico</p>
          <p className={`detail-stat-val${alert.stockfisico < alert.stockteorico ? ' neg' : ''}`}>
            {fmtNum(alert.stockfisico)}
          </p>
        </div>
        <div>
          <p className="detail-stat-lbl">Costo prom.</p>
          <p className="detail-stat-val">{fmtMoney(alert.costopromedio)}</p>
        </div>
        <div>
          <p className="detail-stat-lbl">Score</p>
          <p className="detail-stat-val mono">{alert.score.toFixed(2)}</p>
        </div>
      </div>

      {alert.stockteorico > 0 && (
        <div className="detail-bar-wrap">
          <div className="detail-bar-lbl">
            <span>Stock físico vs. teórico</span>
            <span>{fisicoPct.toFixed(1)}%</span>
          </div>
          <div className="bar-dual">
            <div
              className="bar-fill"
              style={{ width: `${fisicoPct}%`, background: alert.diferencia < 0 ? 'var(--danger)' : 'var(--olive-500)' }}
            >
              {fisicoPct > 15 && <span>{fmtNum(alert.stockfisico)}</span>}
            </div>
          </div>
          <div className="bar-legend">
            <span className="bar-legend-item">
              <span className="bar-legend-swatch" style={{ background: 'var(--olive-500)' }} />
              Físico
            </span>
            <span className="bar-legend-item">
              <span className="bar-legend-swatch" style={{ background: 'var(--muted-2)', border: '1px solid var(--border)' }} />
              Teórico
            </span>
          </div>
        </div>
      )}

      <div className="detail-meta">
        <div className="detail-meta-row">
          <span className="detail-meta-lbl">Almacén</span>
          <span className="detail-meta-val">{alert.almacen_nombre}</span>
        </div>
        <div className="detail-meta-row">
          <span className="detail-meta-lbl">Encargado</span>
          <span className="detail-meta-val">{alert.almacen_encargado}</span>
        </div>
        <div className="detail-meta-row">
          <span className="detail-meta-lbl">Fecha cierre</span>
          <span className="detail-meta-val">{fmtDate(alert.inventariomes_fecha)}</span>
        </div>
        <div className="detail-meta-row">
          <span className="detail-meta-lbl">Ingreso compra</span>
          <span className="detail-meta-val">{fmtNum(alert.ingresocompra)}</span>
        </div>
        <div className="detail-meta-row">
          <span className="detail-meta-lbl">Egreso venta</span>
          <span className="detail-meta-val">{fmtNum(alert.egresoventa)}</span>
        </div>
        {alert.aclaracion && (
          <div className="detail-meta-row">
            <span className="detail-meta-lbl">Aclaración</span>
            <span className="detail-meta-val" style={{ fontSize: 12, textAlign: 'right' }}>{alert.aclaracion}</span>
          </div>
        )}
      </div>

      <div className="detail-actions">
        {isResolved ? (
          <button className="btn btn-ghost" style={{ width: '100%' }} onClick={onReopen}>
            Reabrir alerta
          </button>
        ) : (
          <button className="btn btn-primary" style={{ width: '100%' }} onClick={onMarkRevisada}>
            ✓ Marcar como revisada
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function AlertDashboard() {
  const [closures, setClosures] = useState<ClosureListItem[]>([]);
  const [selectedClosureId, setSelectedClosureId] = useState<number | null>(null);
  const [alerts, setAlerts] = useState<DashboardAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [almacenNombre, setAlmacenNombre] = useState('');
  const [fechaCierre, setFechaCierre] = useState<Date | null>(null);

  const [filterTipo, setFilterTipo] = useState<FilterTipo>('all');
  const [filterSeverity, setFilterSeverity] = useState<FilterSeverity>('all');
  const [filterCategory, setFilterCategory] = useState<FilterCategory>('all');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<SortBy>('score');
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [revisadas, setRevisadas] = useState<Set<string>>(new Set());
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const rightColRef = useRef<HTMLDivElement>(null);

  // Fetch closure list on mount
  useEffect(() => {
    listRecentClosures({ months: 24, limit: 60 })
      .then(data => {
        setClosures(data);
        if (data.length > 0) {
          const preferred = data.find((c: { idinventariomes: number }) => c.idinventariomes === 118888);
          setSelectedClosureId(preferred ? preferred.idinventariomes : data[0].idinventariomes);
        }
      })
      .catch(e => setError(String(e.message)));
  }, []);

  // Fetch report when closure changes
  useEffect(() => {
    if (!selectedClosureId) return;
    setLoading(true);
    setError(null);
    getLocalReport(selectedClosureId)
      .then(report => {
        if (report.header) {
          const mapped = mapFindings(report.findings, report.context_by_idproducto, report.header);
          setAlerts(mapped);
          setAlmacenNombre(report.header.almacen_nombre ?? `Almacén ${report.header.idalmacen}`);
          setFechaCierre(report.header.fecha ? new Date(report.header.fecha) : null);
        } else {
          setAlerts([]);
        }
        setSelectedAlertId(null);
        setRevisadas(new Set());
        setFilterTipo('all');
        setFilterSeverity('all');
        setFilterCategory('all');
      })
      .catch(e => setError(String(e.message)))
      .finally(() => setLoading(false));
  }, [selectedClosureId]);

  // Scroll detail panel into view on mobile when an alert is selected
  useEffect(() => {
    if (selectedAlertId && rightColRef.current && window.innerWidth <= 1080) {
      rightColRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [selectedAlertId]);

  // Unique categories sorted alphabetically
  const categories = useMemo(() => {
    const set = new Set(alerts.map(a => a.producto_cat_nombre).filter(Boolean));
    return Array.from(set).sort();
  }, [alerts]);

  // Filtered + sorted alerts
  const visible = useMemo(() => {
    return alerts
      .filter(a => {
        const isResolved = revisadas.has(a.id);
        if (filterTipo === 'resolved') return isResolved;
        if (isResolved) return false;
        if (filterTipo !== 'all' && a.tipo !== filterTipo) return false;
        if (filterSeverity !== 'all' && a.severity_label !== filterSeverity) return false;
        if (filterCategory !== 'all' && a.producto_cat_nombre !== filterCategory) return false;
        if (search) {
          const q = search.toLowerCase();
          return a.producto_nombre.toLowerCase().includes(q) || a.message.toLowerCase().includes(q);
        }
        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'score') return b.score - a.score;
        if (sortBy === 'mxn') return Math.abs(b.difimporte) - Math.abs(a.difimporte);
        return Math.abs(b.diferencia) - Math.abs(a.diferencia);
      });
  }, [alerts, filterTipo, filterSeverity, filterCategory, search, sortBy, revisadas]);

  const selectedAlert = useMemo(
    () => alerts.find(a => a.id === selectedAlertId) ?? null,
    [alerts, selectedAlertId],
  );

  // Counts
  const counts = useMemo(() => ({
    loss: alerts.filter(a => a.tipo === 'loss' && !revisadas.has(a.id)).length,
    surplus: alerts.filter(a => a.tipo === 'surplus' && !revisadas.has(a.id)).length,
    missing: alerts.filter(a => a.tipo === 'missing' && !revisadas.has(a.id)).length,
    resolved: revisadas.size,
  }), [alerts, revisadas]);

  const lossImpact = useMemo(
    () => alerts.filter(a => a.tipo === 'loss').reduce((s, a) => s + Math.abs(a.difimporte), 0),
    [alerts],
  );
  const surplusImpact = useMemo(
    () => alerts.filter(a => a.tipo === 'surplus').reduce((s, a) => s + a.difimporte, 0),
    [alerts],
  );

  const showToast = useCallback((msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 2500);
  }, []);

  function markRevisada(id: string) {
    setRevisadas(prev => new Set([...prev, id]));
    showToast('Alerta marcada como revisada');
  }

  function reopenAlert(id: string) {
    setRevisadas(prev => { const n = new Set(prev); n.delete(id); return n; });
    showToast('Alerta reabierta');
  }

  // Severity chip data
  const severityChips: { label: string; val: FilterSeverity }[] = [
    { label: 'Todas', val: 'all' },
    { label: 'CRÍTICA', val: 'CRITICA' },
    { label: 'ALTA', val: 'ALTA' },
    { label: 'MEDIA', val: 'MEDIA' },
    { label: 'BAJA', val: 'BAJA' },
  ];

  return (
    <div className="app">
      {/* ── TopBar ── */}
      <header className="topbar">
        <div className="logo">
          <div className="logo-mark">
            <Image src="/talos_logo.png" alt="Talos" width={28} height={28} />
          </div>
          TALOS
        </div>
        <nav className="nav">
          <a href="#" className="active">Alertas</a>
        </nav>
        <PulpoMascot />
        <div className="topbar-right">
          <div className="search">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="2.5">
              <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
            </svg>
            <input
              placeholder="Buscar producto o alerta…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div className="avatar">A</div>
        </div>
      </header>

      {loading && (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink-500)' }}>
          Cargando cierre…
        </div>
      )}

      {error && (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--danger)' }}>
          Error: {error}
        </div>
      )}

      {!loading && !error && (
        <main className="main">
          {/* ── Left Column ── */}
          <div className="left-col">
            <div className="donut-card">
              <DonutChart alerts={alerts} revisadas={revisadas} />
              <p className="donut-title">{almacenNombre}</p>
              <p className="donut-subtitle">{fechaCierre ? fmtDate(fechaCierre) : '—'}</p>
              <div className="kpi-row">
                <div className="kpi">
                  <p className="kpi-num" style={{ color: 'var(--danger)' }}>{fmtMoney(lossImpact)}</p>
                  <p className="kpi-lbl">Faltantes</p>
                </div>
                <div className="kpi">
                  <p className="kpi-num" style={{ color: '#92400E' }}>{fmtMoney(surplusImpact)}</p>
                  <p className="kpi-lbl">Sobrantes</p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="filter-group">
                <p className="filter-label">Cierre</p>
                <select
                  className="select-box"
                  value={selectedClosureId ?? ''}
                  onChange={e => setSelectedClosureId(Number(e.target.value))}
                >
                  {closures.map(c => (
                    <option key={c.idinventariomes} value={c.idinventariomes}>
                      #{c.idinventariomes} · {c.almacen_nombre ?? `Almacén ${c.idalmacen}`} · {c.fecha?.slice(0, 10) ?? '—'}
                    </option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <p className="filter-label">Tipo</p>
                <div className="chip-row">
                  {(['all', 'loss', 'surplus', 'missing', 'resolved'] as FilterTipo[]).map(t => {
                    const cnt = t === 'all' ? alerts.length - revisadas.size
                      : t === 'resolved' ? counts.resolved
                      : counts[t as AlertTipo];
                    return (
                      <button
                        key={t}
                        className={`chip${filterTipo === t ? ' active' : ''}`}
                        onClick={() => setFilterTipo(t)}
                      >
                        {t === 'all' ? 'Todos' : TIPO_LABEL[t as AlertTipo | 'resolved']}
                        <span className="count">{cnt}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="filter-group">
                <p className="filter-label">Severidad</p>
                <div className="chip-row">
                  {severityChips.map(({ label, val }) => {
                    const cnt = val === 'all' ? alerts.length
                      : alerts.filter(a => a.severity_label === val).length;
                    return (
                      <button
                        key={val}
                        className={`chip${filterSeverity === val ? ' active' : ''}`}
                        onClick={() => setFilterSeverity(val)}
                      >
                        {label}
                        <span className="count">{cnt}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="filter-group">
                <p className="filter-label">Categoría</p>
                <div className="chip-row">
                  <button
                    className={`chip${filterCategory === 'all' ? ' active' : ''}`}
                    onClick={() => setFilterCategory('all')}
                  >
                    Todas
                    <span className="count">{alerts.length}</span>
                  </button>
                  {categories.map(cat => (
                    <button
                      key={cat}
                      className={`chip${filterCategory === cat ? ' active' : ''}`}
                      onClick={() => setFilterCategory(cat)}
                    >
                      {cat}
                      <span className="count">{alerts.filter(a => a.producto_cat_nombre === cat).length}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* ── Middle Column ── */}
          <div className="middle-col">
            {/* Summary strip */}
            <div className="summary-strip">
              {(['loss', 'surplus', 'missing', 'resolved'] as const).map(t => {
                const cnt = counts[t === 'loss' ? 'loss' : t === 'surplus' ? 'surplus' : t === 'missing' ? 'missing' : 'resolved'];
                const impact = t === 'loss' ? fmtMoney(lossImpact) : t === 'surplus' ? fmtMoney(surplusImpact) : null;
                return (
                  <button
                    key={t}
                    className={`summary-tile ${t}`}
                    onClick={() => setFilterTipo(filterTipo === t ? 'all' : t)}
                  >
                    <div className="summary-num">{cnt}</div>
                    <div className="summary-lbl">{TIPO_LABEL[t]}</div>
                    {impact && <div className="summary-sub">{impact}</div>}
                    <div className="summary-bg-shape" />
                  </button>
                );
              })}
            </div>

            {/* Alert list */}
            <div className="alert-list">
              <div className="alert-list-header">
                <span className="alert-list-title">
                  Alertas de inventario
                  <span style={{ fontSize: 13, fontWeight: 400, color: 'var(--ink-500)', marginLeft: 8 }}>
                    {visible.length} resultado{visible.length !== 1 ? 's' : ''}
                  </span>
                </span>
                <select
                  className="sort-select"
                  value={sortBy}
                  onChange={e => setSortBy(e.target.value as SortBy)}
                >
                  <option value="score">Ordenar: Score</option>
                  <option value="mxn">Ordenar: Impacto MXN</option>
                  <option value="diff">Ordenar: Diferencia</option>
                </select>
              </div>

              <div className="alert-head-row">
                <span />
                <span>Producto</span>
                <span>Categoría</span>
                <span>Diferencia</span>
                <span>Impacto MXN</span>
                <span>Severidad</span>
                <span>Tipo</span>
              </div>

              <div className="list-scroll">
                {visible.length === 0 && (
                  <div className="empty-state">
                    <div className="empty-state-icon">
                      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--ink-300)" strokeWidth="1.5">
                        <path d="M9 12h6m-3-3v6M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                      </svg>
                    </div>
                    <p>Sin alertas para los filtros seleccionados</p>
                  </div>
                )}
                {visible.map(a => {
                  const isResolved = revisadas.has(a.id);
                  const isSel = a.id === selectedAlertId;
                  return (
                    <div
                      key={a.id}
                      className={`alert-row${isSel ? ' selected' : ''}`}
                      onClick={() => setSelectedAlertId(isSel ? null : a.id)}
                    >
                      <span
                        className={`sev-dot ${isResolved ? 'resolved' : a.tipo}`}
                      />
                      <span>
                        <p className="prod-name">{a.producto_nombre}</p>
                        <p className="prod-sub">{a.message}</p>
                      </span>
                      <span style={{ color: 'var(--ink-500)', fontSize: 12 }}>{a.producto_cat_nombre}</span>
                      <span className={`cell-num${a.diferencia < 0 ? ' neg' : a.diferencia > 0 ? ' pos' : ''}`}>
                        {fmtNum(a.diferencia)}
                      </span>
                      <span className={`cell-num${a.difimporte < 0 ? ' neg' : a.difimporte > 0 ? ' pos' : ''}`}>
                        {fmtMoney(a.difimporte)}
                      </span>
                      <SevTag sev={a.severity_label} isResolved={isResolved} />
                      <TipoTag tipo={a.tipo} isResolved={isResolved} />
                    </div>
                  );
                })}
              </div>

              <div className="pagination">
                <span>Mostrando {visible.length} de {alerts.length} alertas</span>
              </div>
            </div>
          </div>

          {/* ── Right Column ── */}
          <div className="right-col" ref={rightColRef}>
            {selectedAlert ? (
              <DetailPanel
                alert={selectedAlert}
                isResolved={revisadas.has(selectedAlert.id)}
                onMarkRevisada={() => markRevisada(selectedAlert.id)}
                onReopen={() => reopenAlert(selectedAlert.id)}
              />
            ) : (
              <div className="card" style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--ink-500)' }}>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--ink-300)" strokeWidth="1.5" style={{ margin: '0 auto 12px', display: 'block' }}>
                  <path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                  <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7Z" />
                </svg>
                <p style={{ fontSize: 14, fontWeight: 500 }}>Selecciona una alerta para ver el detalle</p>
              </div>
            )}
            <TrendChart alerts={alerts} selectedId={selectedAlertId} />
            <ActivityFeed alerts={alerts} />
          </div>
        </main>
      )}

      {/* ── Toast ── */}
      <div className={`toast${toastMsg ? ' show' : ''}`}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M20 6 9 17l-5-5" />
        </svg>
        {toastMsg}
      </div>
    </div>
  );
}
