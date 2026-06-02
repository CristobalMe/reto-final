import { isBrowser } from "./env.js";

const SESSION_KEY = "autoab:sessionId";

export function getSessionId(): string {
  if (!isBrowser()) return "ssr";
  try {
    let id = sessionStorage.getItem(SESSION_KEY);
    if (!id) {
      id = crypto.randomUUID?.() ?? Math.random().toString(36).slice(2);
      sessionStorage.setItem(SESSION_KEY, id);
    }
    return id;
  } catch {
    return "fallback";
  }
}
