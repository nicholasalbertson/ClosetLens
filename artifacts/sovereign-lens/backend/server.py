#!/usr/bin/env python3
"""Sovereign Lens backend (stdlib only).
Optional API key auth via SOVEREIGN_API_KEY env or --key flag.
"""
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(ROOT), "data")

API_KEY = os.environ.get("SOVEREIGN_API_KEY", "")
if "--key" in sys.argv:
    try:
        API_KEY = sys.argv[sys.argv.index("--key") + 1]
    except Exception:
        pass

def load_json(name):
    path = os.path.join(DATA, name)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

PRODUCTS = load_json("products.json")
ARCHIVE = load_json("archive.json")
OUTFIT_ITEMS = load_json("outfit_system_items.json")
OUTFIT_SUMMARY = load_json("outfit_system_summary.json")

def score_outfit(items, palette, twin_on=False):
    colors = set()
    for it in items:
        for c in it.get("colors", []):
            colors.add(c.lower())
    preferred = {c.lower() for c in palette}
    inter = len(colors & preferred)
    palette_harmony = 0.5 if not colors else min(1.0, 0.4 + 0.6 * inter / max(1, len(colors)))
    has_black = "black" in colors or "charcoal" in colors
    identity = 0.92 if has_black else 0.72
    owned = sum(1 for i in items if i.get("owned"))
    wardrobe = min(1.0, 0.5 + owned / max(1, len(items)) * 0.5)
    twin_bonus = 0.0
    if twin_on:
        names = " ".join(i.get("style_name", "") for i in items).lower()
        if "tunnel" in names: twin_bonus += 0.08
        if "frame" in names: twin_bonus += 0.06
        if has_black: twin_bonus += 0.04
    total = min(1.0, identity * 0.30 + 0.75 * 0.25 + palette_harmony * 0.15 + 0.85 * 0.15 + wardrobe * 0.15 + twin_bonus)
    return round(total, 4), {
        "palette_harmony": round(palette_harmony, 4),
        "identity_alignment": identity,
        "wardrobe_leverage": round(wardrobe, 4),
        "twin_bonus": round(twin_bonus, 4),
    }

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(ROOT), **kwargs)

    def _check_auth(self):
        if not API_KEY:
            return True
        auth = self.headers.get("Authorization", "")
        xkey = self.headers.get("X-API-Key", "")
        if auth == f"Bearer {API_KEY}" or xkey == API_KEY:
            return True
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b'{"error":"unauthorized","hint":"Send Authorization: Bearer <key> or X-API-Key"}')
        return False

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key")
        self.end_headers()

    def do_GET(self):
        if not self._check_auth() and self.path.startswith("/api/"):
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self._json({
                "status": "ok",
                "auth_required": bool(API_KEY),
                "products": len(PRODUCTS),
                "archive": len(ARCHIVE),
                "version": "0.3.0"
            })
        elif parsed.path == "/api/products":
            self._json(PRODUCTS)
        elif parsed.path == "/api/archive":
            self._json(ARCHIVE)
        elif parsed.path == "/api/outfit-system":
            self._json(OUTFIT_SUMMARY)
        elif parsed.path == "/api/outfit-items":
            self._json(OUTFIT_ITEMS[:200])
        else:
            super().do_GET()

    def do_POST(self):
        if not self._check_auth():
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}
        if self.path == "/api/compose":
            self._handle_compose(data)
        elif self.path == "/api/twin-prompt":
            self._handle_twin(data)
        else:
            self.send_error(404)

    def _handle_compose(self, data):
        palette = data.get("palette", ["black"])
        owned_only = data.get("owned_only", False)
        twin = data.get("twin_bias", False)
        budget = data.get("budget_max")
        pool = [p for p in PRODUCTS if not owned_only or p.get("owned")]
        results = []
        for i in range(min(10, len(pool))):
            items = []
            for typ in ["top", "bottom", "footwear", "outerwear", "accessory"]:
                cands = [p for p in pool if p["product_type"] == typ]
                if cands:
                    items.append(cands[i % len(cands)])
            if len(items) < 3:
                continue
            price = sum(p["price"] for p in items)
            if budget and price > budget:
                continue
            total, breakdown = score_outfit(items, palette, twin)
            results.append({
                "id": "S-" + "-".join(p["id"] for p in items),
                "items": items,
                "score": total,
                "breakdown": breakdown,
                "price": price,
            })
        results.sort(key=lambda x: -x["score"])
        self._json(results[:6])

    def _handle_twin(self, data):
        tunnels = data.get("tunnels", True)
        frames = data.get("frames", True)
        physique = data.get("physique", True)
        tattoos = data.get("tattoos", True)
        notes = data.get("notes", "")
        pos = [
            "full body portrait of athletic male",
            "broad shoulders, tapered waist, muscular but lean" if physique else "",
            "4-inch stretched earlobes with large black tunnels, clearly visible, not earrings" if tunnels else "",
            "thick black acetate rectangular optical frames" if frames else "",
            "visible neck script tattoo, hand tattoos, chest ink" if tattoos else "",
            "black luxury streetwear, silver jewelry, chiaroscuro lighting, high detail, cinematic",
            notes,
        ]
        positive = ", ".join(p for p in pos if p)
        negative = "ugly, deformed, mutated, extra limbs, bad anatomy, bad hands, missing fingers, smooth skin, no tattoos, small ears, normal earrings, smiling, bright lighting, cluttered background, text, watermark, female, feminine, soft lighting, gold jewelry, over-exposed"
        self._json({"positive": positive, "negative": negative})

    def _json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Sovereign Lens server on http://localhost:{port}")
    if API_KEY:
        print("API key authentication ENABLED")
    else:
        print("API key authentication DISABLED (set SOVEREIGN_API_KEY or --key)")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
