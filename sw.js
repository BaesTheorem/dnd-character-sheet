/* Offline cache for the hosted (Add to Home Screen) build of the D&D character sheet.
   Only used when the sheet is served over http(s); a locally-opened file never registers this.

   Strategy — bulletproof against a stale/broken cache (a bad build must NEVER strand a user):
   - The main DOCUMENT (the navigation request for index.html) is NETWORK-FIRST. When online we
     always fetch the freshest build with a revalidating request (a cheap 304 when nothing changed,
     a full download only on a real new deploy) and fall back to the cached copy ONLY when the
     network is unreachable. This is what guarantees freshness: the service worker — not the app's
     (possibly broken) JavaScript — owns it, so a corrupt cached build can't wedge an online user.
   - Everything else (manifest, icons, version.json, …) is stale-while-revalidate for speed.
   The activate step deletes every cache except the current one, so nothing lingers across deploys.
   CACHE is auto-stamped to the app version by .githooks/pre-commit on every commit. */
const CACHE = "dnd-sheet-v490";
const DOC = "./index.html";

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", e => e.waitUntil(
  caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim())
));

// The document: try the network first (revalidating), cache only as an offline fallback.
async function networkFirstDoc(req){
  const cache = await caches.open(CACHE);
  try{
    const net = await fetch(req, { cache: "no-cache" });   // always revalidate with the server
    if(net && net.ok){ cache.put(DOC, net.clone()); return net; }
    throw new Error("bad status " + (net && net.status));
  }catch(_){
    return (await cache.match(req)) || (await cache.match(DOC)) ||
      new Response("Offline, and no copy is cached yet. Reconnect once to install it.",
        { status: 503, statusText: "Offline" });
  }
}

// Everything else: serve cached instantly, refresh the cache in the background.
async function staleWhileRevalidate(req){
  const cache = await caches.open(CACHE);
  const cached = await cache.match(req);
  const network = fetch(req).then(res => { if(res && res.ok) cache.put(req, res.clone()); return res; }).catch(() => null);
  return cached || (await network) || new Response("Offline and not cached yet.", { status: 503, statusText: "Offline" });
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if(req.method !== "GET") return;
  // Treat the top-level HTML load as the document (network-first). mode==="navigate" covers real
  // navigations; the destination / Accept checks are a cross-browser backstop for the same thing.
  const isDoc = req.mode === "navigate" || req.destination === "document" ||
                (req.headers.get("accept") || "").includes("text/html");
  e.respondWith(isDoc ? networkFirstDoc(req) : staleWhileRevalidate(req));
});
