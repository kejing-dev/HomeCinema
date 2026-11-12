"""Static server for frame-lab + POST /save?name=<file> writes the body to out/<file>. Usage: python3 serve.py <port>"""
import http.server, os, sys, urllib.parse
ROOT = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(ROOT, os.environ.get("LAB_OUT","out"))
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(self, *a): pass
    def do_POST(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        name = os.path.basename(q["name"][0]); n = int(self.headers["Content-Length"])
        open(os.path.join(OUT, name), "wb").write(self.rfile.read(n))
        self.send_response(200); self.send_header("Content-Type", "text/plain"); self.end_headers(); self.wfile.write(b"ok")
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
