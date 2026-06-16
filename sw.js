/* Offline cache for the hosted (Add to Home Screen) build of the D&D character sheet.
   Only used when the sheet is served over http(s); a locally-opened file never registers this.
   Strategy: stale-while-revalidate — serve the cached copy instantly (works fully offline once
   it has been loaded online once), and refresh the cache in the background so edits flow through
   on the next launch. CACHE is auto-stamped to the app version by .githooks/pre-commit on every
   commit, so each deploy drops the old cache and fresh content lands on the next load (no manual
   bump, no "reload twice"). */
const CACHE = "dnd-sheet-v230";

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", e => e.waitUntil(
  caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim())
));

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  e.respondWith(caches.open(CACHE).then(async cache => {
    const cached = await cache.match(req);
    const network = fetch(req).then(res => {
      if (res && res.ok) cache.put(req, res.clone());   // keep the cache warm for next time
      return res;
    }).catch(() => null);
    return cached || (await network) || new Response("Offline and not cached yet.", { status: 503, statusText: "Offline" });
  }));
});
