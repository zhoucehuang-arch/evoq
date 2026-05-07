#!/usr/bin/env python3
import json
import re
import time
from html import unescape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, quote_plus, urlparse
from urllib.request import Request, urlopen

HOST = "127.0.0.1"
PORT = 8888
USER_AGENT = "Mozilla/5.0 (OpenClaw-SearxCompat/1.0)"


def _fetch_duckduckgo_html(query: str) -> str:
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=12) as resp:
        return resp.read().decode("utf-8", "ignore")


def _extract_results(html: str, limit: int = 10):
    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
        r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
        re.S,
    )
    out = []
    for match in pattern.finditer(html):
        url = unescape(re.sub(r"\s+", " ", match.group("url")).strip())
        title = unescape(re.sub(r"<[^>]+>", "", match.group("title"))).strip()
        snippet = unescape(re.sub(r"<[^>]+>", "", match.group("snippet"))).strip()
        if not url or not title:
            continue
        out.append(
            {
                "url": url,
                "title": title,
                "content": snippet,
                "engine": "duckduckgo_html",
                "score": 1.0,
                "source_quality": "medium",
                "freshness": "unknown",
                "corroboration": "single_source",
            }
        )
        if len(out) >= limit:
            break
    return out


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, payload: dict):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path in ("/", "/health"):
            return self._json(
                200,
                {
                    "status": "ok",
                    "service": "searxng-compat",
                    "provider": "duckduckgo_html",
                    "time": int(time.time()),
                },
            )

        if parsed.path == "/search":
            query = (qs.get("q") or [""])[0].strip()
            out_format = (qs.get("format") or ["json"])[0]
            if not query:
                return self._json(400, {"error": "missing q"})
            if out_format != "json":
                return self._json(400, {"error": "only format=json supported"})
            try:
                html = _fetch_duckduckgo_html(query)
                results = _extract_results(html)
                return self._json(
                    200,
                    {
                        "query": query,
                        "number_of_results": len(results),
                        "results": results,
                        "search_provider": "searxng-compat",
                        "fallback_status": "duckduckgo_html",
                    },
                )
            except Exception as exc:
                return self._json(
                    502,
                    {
                        "error": "upstream_failed",
                        "detail": str(exc),
                        "search_provider": "searxng-compat",
                        "fallback_status": "blocked",
                    },
                )

        return self._json(404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        return


def main():
    server = HTTPServer((HOST, PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
