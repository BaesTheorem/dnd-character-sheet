#!/usr/bin/env python3
"""Local stand-in for GitHub Pages: serves --root with gzip on .html/.js/.json, the way Pages does,
so transfer size and paint timing match the live site. The landing page tests start it themselves."""
import argparse, functools, gzip, http.server, mimetypes, os, socketserver

class H(http.server.SimpleHTTPRequestHandler):
    cache = {}
    def log_message(self, *a): pass
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()
    def do_GET(self):
        path = self.translate_path(self.path.split("?")[0].split("#")[0])
        if os.path.isdir(path): path = os.path.join(path, "index.html")
        if not os.path.isfile(path): return self.send_error(404)
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if path.endswith(".webmanifest"): ctype = "application/manifest+json"
        st = os.stat(path); key = (path, st.st_mtime_ns, st.st_size)
        raw = open(path, "rb").read()
        gz = "gzip" in (self.headers.get("Accept-Encoding") or "") and path.endswith((".html", ".js", ".json", ".webmanifest"))
        body = raw
        if gz:
            if key not in H.cache: H.cache = {key: gzip.compress(raw, 6)} if len(raw) > 1_000_000 else {**H.cache, key: gzip.compress(raw, 6)}
            body = H.cache[key]
        self.send_response(200)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text/") else ""))
        if gz: self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "max-age=600")
        self.end_headers()
        try: self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError): pass

class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--root", required=True); ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    S(("127.0.0.1", a.port), functools.partial(H, directory=a.root)).serve_forever()
