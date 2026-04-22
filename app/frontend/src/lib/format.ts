const MXN_FMT = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
});

const NUM_FMT = new Intl.NumberFormat("es-MX", { maximumFractionDigits: 2 });

const DATE_FMT = new Intl.DateTimeFormat("es-MX", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

export function fmtMoney(n: number, withSign = false): string {
  const sign = n > 0 && withSign ? "+" : "";
  return sign + MXN_FMT.format(n);
}

export function fmtNum(n: number, unit?: string | null): string {
  const base = NUM_FMT.format(n);
  return unit ? `${base} ${unit}` : base;
}

export function fmtDate(d: Date | null): string {
  if (!d) return "—";
  return DATE_FMT.format(d);
}
