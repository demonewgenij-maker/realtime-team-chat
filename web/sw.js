// Service worker: cache the app shell for an offline-friendly PWA.
const CACHE = "team-chat-shell-v1";
const SHELL = [
  "/",
  "/index.html",
  "/app.js",
  "/style.css",
  "/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  // Never cache API or WebSocket traffic — only the static shell.
  const url = new URL(request.url);
  if (request.method !== "GET" || url.pathname.startsWith("/api") || url.pathname === "/ws") {
    return;
  }
  // Network-first for navigations, cache fallback when offline.
  event.respondWith(
    fetch(request)
      .then((resp) => {
        const copy = resp.clone();
        caches.open(CACHE).then((c) => c.put(request, copy));
        return resp;
      })
      .catch(() => caches.match(request).then((r) => r || caches.match("/index.html")))
  );
});
