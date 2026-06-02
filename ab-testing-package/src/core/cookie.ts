import type { CookieDecision, CookieOptions } from "../types.js";
import { isBrowser } from "./env.js";

const PREFIX = "autoab:";

export function readDecision(key: string): CookieDecision | null {
  if (!isBrowser()) return null;
  const name = PREFIX + key + "=";
  const parts = document.cookie.split(";");
  for (const part of parts) {
    const trimmed = part.trim();
    if (trimmed.startsWith(name)) {
      try {
        return JSON.parse(decodeURIComponent(trimmed.slice(name.length)));
      } catch {
        return null;
      }
    }
  }
  return null;
}

export function writeDecision(
  key: string,
  decision: CookieDecision,
  ttlMs: number,
  opts: CookieOptions = {}
): void {
  if (!isBrowser()) return;
  if (opts.enabled === false) return;

  const value = encodeURIComponent(JSON.stringify(decision));
  const expires = new Date(Date.now() + ttlMs).toUTCString();
  const path = opts.path ?? "/";
  const sameSite = opts.sameSite ?? "Lax";
  const secure = opts.secure ? "; Secure" : "";

  document.cookie = `${PREFIX}${key}=${value}; expires=${expires}; path=${path}; SameSite=${sameSite}${secure}`;
}
