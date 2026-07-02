#!/usr/bin/env python3
"""Small reverse proxy gateway for the four-app GTM First Touch workflow."""
from __future__ import annotations

import argparse
import http.server
import urllib.error
import urllib.request


DEFAULT_PORT = 8000

ROUTES = {
    "/discovery": ("127.0.0.1", 3005),
    "/outbound-email": ("127.0.0.1", 3008),
    "/enrichment": ("127.0.0.1", 3011),
    "/icp-scorer": ("127.0.0.1", 3012),
}

HUB_PAGE = """\
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GTM First Touch</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      min-height: 100vh;
      background: #171717;
      color: #e8e4dc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    main { max-width: 1080px; margin: 0 auto; padding: 56px 28px; }
    header { margin-bottom: 34px; }
    .eyebrow { color: #8aa7a0; font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
    h1 { color: #fff; font-size: 36px; line-height: 1.1; margin: 8px 0 10px; }
    .subtitle { color: #aaa39a; font-size: 16px; max-width: 720px; line-height: 1.55; }
    .path {
      display: flex; flex-wrap: wrap; gap: 8px; margin: 28px 0 34px;
      color: #bdb7ae; font-size: 14px;
    }
    .step-pill { border: 1px solid #3a3732; border-radius: 999px; padding: 7px 11px; background: #20201e; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
    @media (max-width: 900px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
    @media (max-width: 560px) { main { padding: 36px 16px; } .grid { grid-template-columns: 1fr; } }
    a.card {
      display: flex; flex-direction: column; min-height: 230px;
      border: 1px solid #312f2a; border-radius: 8px;
      background: #22211f; color: inherit; text-decoration: none; overflow: hidden;
      transition: transform .14s ease, border-color .14s ease, background .14s ease;
    }
    a.card:hover { transform: translateY(-2px); border-color: #7a8f88; background: #292825; }
    .top { height: 78px; display: flex; align-items: center; padding: 0 18px; color: #1a1a1a; font-weight: 800; }
    .one { background: #b5c4b1; }
    .two { background: #d4a090; }
    .three { background: #a3bdd4; }
    .four { background: #c4bba8; }
    .body { padding: 18px; display: flex; flex: 1; flex-direction: column; }
    .num { font-size: 13px; color: #878078; margin-bottom: 8px; }
    .title { font-size: 18px; color: #fff; font-weight: 700; margin-bottom: 8px; }
    .desc { color: #aaa39a; font-size: 14px; line-height: 1.5; flex: 1; }
    .cta { color: #d9d2c6; font-size: 13px; margin-top: 16px; }
  </style>
</head>
<body>
  <main>
    <header>
      <div class="eyebrow">Local GTM workflow</div>
      <h1>GTM First Touch</h1>
      <p class="subtitle">A four-app workflow for turning a target account into a scored, researched, persona-specific first touch and discovery plan.</p>
    </header>

    <div class="path">
      <span class="step-pill">1. Qualify</span>
      <span class="step-pill">2. Research</span>
      <span class="step-pill">3. Write outreach</span>
      <span class="step-pill">4. Prep discovery</span>
    </div>

    <section class="grid">
      <a class="card" href="/icp-scorer/">
        <div class="top one">ICP</div>
        <div class="body">
          <div class="num">Step 1</div>
          <div class="title">ICP Scorer</div>
          <p class="desc">Score whether an account is worth pursuing before spending research or outbound time.</p>
          <div class="cta">Open scorer</div>
        </div>
      </a>
      <a class="card" href="/enrichment/">
        <div class="top two">Research</div>
        <div class="body">
          <div class="num">Step 2</div>
          <div class="title">Enrichment</div>
          <p class="desc">Build account context: company overview, tech stack, funding, hiring, and competitive landscape.</p>
          <div class="cta">Open enrichment</div>
        </div>
      </a>
      <a class="card" href="/outbound-email/">
        <div class="top three">Outreach</div>
        <div class="body">
          <div class="num">Step 3</div>
          <div class="title">Outbound Email</div>
          <p class="desc">Generate persona-specific first-touch messaging from the account research and trigger.</p>
          <div class="cta">Open outbound</div>
        </div>
      </a>
      <a class="card" href="/discovery/">
        <div class="top four">Discovery</div>
        <div class="body">
          <div class="num">Step 4</div>
          <div class="title">Discovery Call Prep</div>
          <p class="desc">Turn the account story into pain hypotheses, discovery questions, and call prep.</p>
          <div class="cta">Open discovery prep</div>
        </div>
      </a>
    </section>
  </main>
</body>
</html>
"""


class GatewayHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._handle()

    def do_POST(self) -> None:
        self._handle()

    def do_PUT(self) -> None:
        self._handle()

    def do_DELETE(self) -> None:
        self._handle()

    def _handle(self) -> None:
        if self.path in ("", "/"):
            self._send_html(HUB_PAGE)
            return

        route_prefix = self._match_route(self.path)
        if not route_prefix:
            self.send_error(404, "Not found")
            return

        if self.path == route_prefix:
            self.send_response(302)
            self.send_header("Location", route_prefix + "/")
            self.end_headers()
            return

        host, port = ROUTES[route_prefix]
        target = f"http://{host}:{port}{self.path}"
        self._proxy(target, route_prefix)

    def _match_route(self, path: str) -> str | None:
        for prefix in sorted(ROUTES, key=len, reverse=True):
            if path == prefix or path.startswith(prefix + "/"):
                return prefix
        return None

    def _proxy(self, target: str, route_prefix: str) -> None:
        body = None
        if self.command in {"POST", "PUT"}:
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(length) if length else None

        headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
        req = urllib.request.Request(target, data=body, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                payload = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() in {"transfer-encoding", "connection"}:
                        continue
                    if key.lower() == "location" and value.startswith("/"):
                        value = route_prefix + value
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            for key, value in exc.headers.items():
                if key.lower() in {"transfer-encoding", "connection"}:
                    continue
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(payload)
        except urllib.error.URLError as exc:
            self.send_error(502, f"Backend unavailable: {exc}")

    def _send_html(self, html: str) -> None:
        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def command_serve(args: argparse.Namespace) -> int:
    port = args.port or DEFAULT_PORT
    server = http.server.HTTPServer(("127.0.0.1", port), GatewayHandler)
    print(f"GTM First Touch gateway running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gateway")
    subparsers = parser.add_subparsers(dest="command")
    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--port", type=int, default=None)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "serve":
        return command_serve(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
