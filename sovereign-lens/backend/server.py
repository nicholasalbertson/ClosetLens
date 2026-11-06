#!/usr/bin/env python3
"""Sovereign Lens local backend (stdlib only).

Auth boundary
-------------
When ``SOVEREIGN_API_KEY`` or ``--key`` is set, every ``/api/*`` request must
send ``Authorization: Bearer <key>`` or ``X-API-Key: <key>``. A failed check
writes exactly one 401 JSON response and returns. It must not fall through to
the static file handler.

Static pages (the Lens UI, backend UI, and docs) stay public so the browser
can load the app and prompt for a key. Catalog JSON under ``data/`` is not
served as files; clients read it from the API.
"""
import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = os.path.dirname(ROOT)
DATA = os.path.join(APP_ROOT, "data")

API_KEY = os.environ.get("SOVEREIGN_API_KEY", "")
if "--key" in sys.argv:
    try:
        API_KEY = sys.argv[sys.argv.index("--key") + 1]
    except Exception:
        pass

PUBLIC_FILES = {
    "/sovereign-lens-v2.html",
    "/sovereign-lens.html",
    "/backend-ui.html",
    "/original-sovereign-closet.html",
    "/ARCHITECTURE.md",
    "/README.md",
}

MAX_BODY = 1_000_000
QUERY_STOPWORDS = {"look", "outfit", "the", "and", "with", "for", "a", "an"}


def load_json(name):
    path = os.path.join(DATA, name)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    return []


PRODUCTS = load_json("products.json")
ARCHIVE = load_json("archive.json")
OUTFIT_ITEMS = load_json("outfit_system_items.json")
OUTFIT_SUMMARY = load_json("outfit_system_summary.json")


def normalize_path(raw_path):
    """Collapse dot segments and duplicate slashes. Query strings are dropped.

    Request targets are paths, not scheme-relative URLs. ``urlparse`` would
    treat ``//docs/...`` as a network location and drop the first segment.
    """
    if raw_path.startswith(("http://", "https://")):
        raw_path = urlparse(raw_path).path or "/"
    path = unquote(raw_path.split("?", 1)[0].split("#", 1)[0] or "/")
    if not path.startswith("/"):
        path = "/" + path
    parts = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/" + "/".join(parts)


def static_allowed(path):
    if path in PUBLIC_FILES:
        return True
    return path.startswith("/docs/") and not path.endswith("/")


def resolve_static(path):
    if not static_allowed(path):
        return None
    root = os.path.realpath(APP_ROOT)
    candidate = os.path.realpath(os.path.join(root, path.lstrip("/")))
    if candidate != root and not candidate.startswith(root + os.sep):
        return None
    if not os.path.isfile(candidate):
        return None
    return candidate


def query_tokens(query):
    tokens = []
    current = []
    for char in (query or "").lower():
        if char.isalnum():
            current.append(char)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return [token for token in tokens if len(token) >= 3 and token not in QUERY_STOPWORDS]


def item_text(product):
    tags = " ".join(product.get("tags") or [])
    return " ".join(
        [
            str(product.get("style_name") or ""),
            str(product.get("brand") or ""),
            tags,
        ]
    ).lower()


def rank_pool(pool, tokens):
    """Prefer catalog rows that mention the query. Empty queries keep file order."""
    if not tokens or not pool:
        return list(pool)

    def hits(product):
        text = item_text(product)
        return sum(1 for token in tokens if token in text)

    matched = [product for product in pool if hits(product) > 0]
    if not matched:
        return list(pool)
    matched.sort(key=hits, reverse=True)
    rest = [product for product in pool if product not in matched]
    return matched + rest


def score_outfit(items, palette, twin_on=False):
    colors = set()
    for item in items:
        for color in item.get("colors", []):
            colors.add(str(color).lower())
    preferred = {str(color).lower() for color in palette}
    overlap = len(colors & preferred)
    palette_harmony = 0.5 if not colors else min(1.0, 0.4 + 0.6 * overlap / max(1, len(colors)))
    has_black = "black" in colors or "charcoal" in colors
    identity = 0.92 if has_black else 0.72
    owned = sum(1 for item in items if item.get("owned"))
    wardrobe = min(1.0, 0.5 + owned / max(1, len(items)) * 0.5)
    twin_bonus = 0.0
    if twin_on:
        names = " ".join(item.get("style_name", "") for item in items).lower()
        if "tunnel" in names:
            twin_bonus += 0.08
        if "frame" in names:
            twin_bonus += 0.06
        if has_black:
            twin_bonus += 0.04
    total = min(
        1.0,
        identity * 0.30
        + 0.75 * 0.25
        + palette_harmony * 0.15
        + 0.85 * 0.15
        + wardrobe * 0.15
        + twin_bonus,
    )
    return round(total, 4), {
        "palette_harmony": round(palette_harmony, 4),
        "identity_alignment": identity,
        "wardrobe_leverage": round(wardrobe, 4),
        "twin_bonus": round(twin_bonus, 4),
    }


def compose_outfits(data):
    palette = data.get("palette") or ["black"]
    owned_only = bool(data.get("owned_only", False))
    twin = bool(data.get("twin_bias", False))
    budget = data.get("budget_max")
    tokens = query_tokens(data.get("query") or "")
    pool = [product for product in PRODUCTS if not owned_only or product.get("owned")]
    results = []
    for index in range(min(10, len(pool))):
        items = []
        for product_type in ["top", "bottom", "footwear", "outerwear", "accessory"]:
            candidates = rank_pool(
                [product for product in pool if product.get("product_type") == product_type],
                tokens,
            )
            if candidates:
                items.append(candidates[index % len(candidates)])
        if len(items) < 3:
            continue
        price = sum(float(product.get("price") or 0) for product in items)
        if budget and price > budget:
            continue
        total, breakdown = score_outfit(items, palette, twin)
        results.append(
            {
                "id": "S-" + "-".join(str(product.get("id")) for product in items),
                "items": items,
                "score": total,
                "breakdown": breakdown,
                "price": price,
                "source": "backend",
                "query": data.get("query") or "",
            }
        )
    results.sort(key=lambda row: -row["score"])
    return results[:6]


def twin_prompt(data):
    tunnels = data.get("tunnels", True)
    frames = data.get("frames", True)
    physique = data.get("physique", True)
    tattoos = data.get("tattoos", True)
    notes = data.get("notes", "")
    positive_parts = [
        "full body portrait of athletic male",
        "broad shoulders, tapered waist, muscular but lean" if physique else "",
        "4-inch stretched earlobes with large black tunnels, clearly visible, not earrings" if tunnels else "",
        "thick black acetate rectangular optical frames" if frames else "",
        "visible neck script tattoo, hand tattoos, chest ink" if tattoos else "",
        "black luxury streetwear, silver jewelry, chiaroscuro lighting, high detail, cinematic",
        notes,
    ]
    positive = ", ".join(part for part in positive_parts if part)
    negative = (
        "ugly, deformed, mutated, extra limbs, bad anatomy, bad hands, missing fingers, "
        "smooth skin, no tattoos, small ears, normal earrings, smiling, bright lighting, "
        "cluttered background, text, watermark, female, feminine, soft lighting, gold jewelry, over-exposed"
    )
    return {"positive": positive, "negative": negative, "source": "backend"}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    server_version = "SovereignLens/0.4"

    def _authorized(self):
        if not API_KEY:
            return True
        auth = self.headers.get("Authorization", "")
        supplied = self.headers.get("X-API-Key", "")
        return auth == f"Bearer {API_KEY}" or supplied == API_KEY

    def _write(self, code, body, content_type):
        """Write one complete response. Callers must return immediately after."""
        if not isinstance(body, bytes):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._write(code, json.dumps(obj), "application/json")

    def _unauthorized(self):
        self._json(
            {
                "error": "unauthorized",
                "hint": "Send Authorization: Bearer <key> or X-API-Key",
            },
            401,
        )

    def _not_found(self):
        self._json({"error": "not_found"}, 404)

    def _path(self):
        return normalize_path(self.path)

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            length = 0
        if length < 0 or length > MAX_BODY:
            return None
        if length == 0:
            return b""
        return self.rfile.read(length)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()

    def do_GET(self):
        path = self._path()
        if path.startswith("/api/"):
            if not self._authorized():
                self._unauthorized()
                return
            self._dispatch_get(path)
            return
        if path in ("/", "/index.html"):
            path = "/sovereign-lens-v2.html"
        full = resolve_static(path)
        if full is None:
            self._not_found()
            return
        content_type = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/javascript":
            content_type += "; charset=utf-8"
        with open(full, "rb") as handle:
            self._write(200, handle.read(), content_type)

    def do_POST(self):
        path = self._path()
        raw = self._read_body()
        if raw is None:
            self._json({"error": "payload_too_large"}, 413)
            return
        if not path.startswith("/api/"):
            self._not_found()
            return
        if not self._authorized():
            self._unauthorized()
            return
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
        if path == "/api/compose":
            self._json(compose_outfits(data))
            return
        if path == "/api/twin-prompt":
            self._json(twin_prompt(data))
            return
        self._not_found()

    def _dispatch_get(self, path):
        if path == "/api/status":
            summaries = OUTFIT_SUMMARY if isinstance(OUTFIT_SUMMARY, list) else []
            items = OUTFIT_ITEMS if isinstance(OUTFIT_ITEMS, list) else []
            self._json(
                {
                    "status": "ok",
                    "auth_required": bool(API_KEY),
                    "products": len(PRODUCTS) if isinstance(PRODUCTS, list) else 0,
                    "archive": len(ARCHIVE) if isinstance(ARCHIVE, list) else 0,
                    "outfit_items": len(items),
                    "outfit_summaries": len(summaries),
                    "version": "0.4.0",
                    "static_auth": False,
                }
            )
            return
        if path == "/api/products":
            self._json(PRODUCTS)
            return
        if path == "/api/archive":
            self._json(ARCHIVE)
            return
        if path == "/api/outfit-system":
            self._json(OUTFIT_SUMMARY)
            return
        if path == "/api/outfit-items":
            items = OUTFIT_ITEMS if isinstance(OUTFIT_ITEMS, list) else []
            self._json(items[:200])
            return
        self._not_found()

    def log_message(self, format, *args):
        return


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    print(f"Sovereign Lens server on http://{host}:{port}")
    if API_KEY:
        print("API key authentication ENABLED for /api/* (static pages stay public)")
    else:
        print("API key authentication DISABLED (set SOVEREIGN_API_KEY or --key)")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
