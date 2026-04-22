import type { ClosureListItem, LocalReport } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function listRecentClosures(params: {
  idsucursal?: number;
  months?: number;
  limit?: number;
} = {}): Promise<ClosureListItem[]> {
  const qs = new URLSearchParams();
  if (params.idsucursal !== undefined) qs.set("idsucursal", String(params.idsucursal));
  if (params.months !== undefined) qs.set("months", String(params.months));
  if (params.limit !== undefined) qs.set("limit", String(params.limit));
  const q = qs.toString();
  return getJson<ClosureListItem[]>(`/closures${q ? `?${q}` : ""}`);
}

export function getLocalReport(idinventariomes: number): Promise<LocalReport> {
  return getJson<LocalReport>(`/metrics/local/${idinventariomes}`);
}
