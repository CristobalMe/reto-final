import "@testing-library/jest-dom";

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
  constructor(public callback: IntersectionObserverCallback) {}
}
Object.defineProperty(window, "IntersectionObserver", {
  writable: true,
  value: MockIntersectionObserver,
});

// Mock crypto.randomUUID if not present
if (!globalThis.crypto) {
  (globalThis as unknown as { crypto: { randomUUID: () => string } }).crypto = {
    randomUUID: () =>
      "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
      }),
  };
}
