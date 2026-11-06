#!/usr/bin/env python3
"""Sovereign Lens backend (stdlib only).
Optional API key auth via SOVEREIGN_API_KEY env or --key flag.
"""
import json
import os
import sys
import time
import hmac
import hashlib
import base64
import urllib.request
import urllib.parse
from collections import defaultdict
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(ROOT), "data")

def load_dotenv():
    env_path = os.path.join(os.path.dirname(ROOT), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_dotenv()
DATA = os.path.join(os.path.dirname(ROOT), "data")

API_KEY = os.environ.get("SOVEREIGN_API_KEY", "")
JWT_SECRET = os.environ.get("JWT_SECRET", API_KEY or "change-me-in-production")
JWT_EXPIRY = int(os.environ.get("JWT_EXPIRY", "86400"))  # 24h default
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8080/api/auth/google/callback")
AFFILIATE_KEY = os.environ.get("AFFILIATE_API_KEY", "")
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "30"))  # requests per minute per IP
_rate_buckets = defaultdict(list)
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

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def jwt_create(payload: dict, secret: str = JWT_SECRET, exp: int = JWT_EXPIRY) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    body = {**payload, "exp": int(time.time()) + exp, "iat": int(time.time())}
    h = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = b64url_encode(json.dumps(body, separators=(",", ":")).encode())
    sig = hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{b64url_encode(sig)}"

def jwt_verify(token: str, secret: str = JWT_SECRET) -> dict | None:
    try:
        h, p, s = token.split(".")
        expected = hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(b64url_decode(s), expected):
            return None
        payload = json.loads(b64url_decode(p))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

def rate_limited(ip: str) -> bool:
    now = time.time()
    window = _rate_buckets[ip]
    # drop entries older than 60s
    window[:] = [t for t in window if now - t < 60]
    if len(window) >= RATE_LIMIT:
        return True
    window.append(now)
    return False

def score_outfit(items, palette, twin_on=False, style_axes=None):
    """Scoring that reads StyleAxes when provided and uses item tags/types for twin enforcement."""
    colors = set()
    for it in items:
        for c in it.get("colors", []) or []:
            colors.add(str(c).lower())
    preferred = {c.lower() for c in (palette or [])}
    inter = len(colors & preferred)
    palette_harmony = 0.5 if not colors else min(1.0, 0.4 + 0.6 * inter / max(1, len(colors)))

    # StyleAxes override or modulate identity
    identity_base = 0.92 if ("black" in colors or "charcoal" in colors) else 0.72
    if style_axes and "identity" in style_axes:
        identity = float(style_axes["identity"])
    else:
        identity = identity_base

    owned = sum(1 for i in items if i.get("owned"))
    wardrobe = min(1.0, 0.5 + owned / max(1, len(items)) * 0.5)

    # Twin enforcement via tags or product_type, not just name substring
    twin_bonus = 0.0
    if twin_on:
        tags = set()
        for it in items:
            for t in it.get("tags", []) or []:
                tags.add(str(t).lower())
            if it.get("product_type") == "accessory":
                name = (it.get("style_name") or "").lower()
                if "tunnel" in name or "tunnel" in tags:
                    twin_bonus += 0.08
                if "frame" in name or "frame" in tags:
                    twin_bonus += 0.06
        if "black" in colors or "charcoal" in colors:
            twin_bonus += 0.04
        # Require at least one twin signal for full bonus credit
        if twin_bonus < 0.06:
            twin_bonus *= 0.3  # partial credit only

    # Silhouette from StyleAxes or default
    silhouette = 0.75
    if style_axes and "silhouette" in style_axes:
        silhouette = float(style_axes["silhouette"])

    total = min(1.0, identity * 0.30 + silhouette * 0.25 + palette_harmony * 0.15 + 0.85 * 0.15 + wardrobe * 0.15 + twin_bonus)
    return round(total, 4), {
        "palette_harmony": round(palette_harmony, 4),
        "identity_alignment": round(identity, 4),
        "wardrobe_leverage": round(wardrobe, 4),
        "twin_bonus": round(twin_bonus, 4),
        "silhouette": round(silhouette, 4),
    }

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(ROOT), **kwargs)

    def _check_auth(self):
        auth = self.headers.get("Authorization", "")
        xkey = self.headers.get("X-API-Key", "")
        # JWT first
        if auth.startswith("Bearer "):
            token = auth[7:]
            if jwt_verify(token):
                return True
        # Fallback to static API key
        if API_KEY and (auth == f"Bearer {API_KEY}" or xkey == API_KEY):
            return True
        if not API_KEY and not JWT_SECRET:
            return True
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b'{"error":"unauthorized","hint":"Send Authorization: Bearer <jwt-or-key>"}')
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
                "gemini_configured": bool(GEMINI_KEY),
                "google_photos_configured": bool(GOOGLE_CLIENT_ID),
                "affiliate_configured": bool(AFFILIATE_KEY),
                "products": len(PRODUCTS),
                "archive": len(ARCHIVE),
                "jwt_enabled": True,
                "version": "0.3.7"
            })
        elif parsed.path == "/api/products":
            self._json(PRODUCTS)
        elif parsed.path == "/api/archive":
            self._json(ARCHIVE)
        elif parsed.path == "/api/outfit-system":
            self._json(OUTFIT_SUMMARY)
        elif parsed.path == "/api/outfit-items":
            self._json(OUTFIT_ITEMS[:200])
        elif parsed.path == "/api/auth/google/start":
            if not GOOGLE_CLIENT_ID:
                self._json({"error": "GOOGLE_CLIENT_ID not set"}, 400)
                return
            scope = "https://www.googleapis.com/auth/photoslibrary.readonly"
            params = urllib.parse.urlencode({
                "client_id": GOOGLE_CLIENT_ID,
                "redirect_uri": GOOGLE_REDIRECT,
                "response_type": "code",
                "scope": scope,
                "access_type": "offline",
                "prompt": "consent",
            })
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"
            self._json({"auth_url": auth_url, "scope": scope})
        elif parsed.path.startswith("/api/auth/google/callback"):
            qs = parse_qs(parsed.query)
            code = (qs.get("code") or [None])[0]
            if not code or not GOOGLE_CLIENT_SECRET:
                self._json({"error": "missing code or secret"}, 400)
                return
            token_data = urllib.parse.urlencode({
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT,
                "grant_type": "authorization_code",
            }).encode()
            try:
                req = urllib.request.Request("https://oauth2.googleapis.com/token", data=token_data)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    tokens = json.loads(resp.read())
                self._json({"access_token": tokens.get("access_token"), "expires_in": tokens.get("expires_in")})
            except Exception as e:
                self._json({"error": str(e)}, 502)
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
        elif self.path == "/api/auth/token":
            # Issue a JWT (demo: any POST with {"sub": "user"} works when API_KEY matches or is unset)
            if API_KEY and not self._check_auth():
                return
            sub = data.get("sub", "user")
            token = jwt_create({"sub": sub})
            self._json({"access_token": token, "token_type": "Bearer", "expires_in": JWT_EXPIRY})
        elif self.path == "/api/compose":
            self._handle_compose(data)
        elif self.path == "/api/twin-prompt":
            self._handle_twin(data)
        elif self.path == "/api/vision":
            self._handle_vision(data)
        elif self.path == "/api/photos/search":
            self._handle_photos(data)
        elif self.path == "/api/affiliate/search":
            self._handle_affiliate(data)
        else:
            self.send_error(404)

    def _handle_compose(self, data):
        import random
        palette = data.get("palette", ["black"])
        owned_only = data.get("owned_only", False)
        twin = data.get("twin_bias", False)
        budget = data.get("budget_max")
        style_axes = data.get("style_axes")
        pool = [p for p in PRODUCTS if not owned_only or p.get("owned")]
        # Exclude underwear from main slots
        types = ["top", "bottom", "footwear", "outerwear", "accessory"]
        by_type = {t: [p for p in pool if p.get("product_type") == t] for t in types}
        results = []
        seen_sigs = set()
        attempts = 0
        max_attempts = 40
        while len(results) < 6 and attempts < max_attempts:
            attempts += 1
            items = []
            for typ in types:
                cands = by_type[typ]
                if not cands:
                    continue
                # Random rotation instead of modulo
                pick = random.choice(cands)
                items.append(pick)
            if len(items) < 3:
                continue
            # Dedup by sorted item IDs
            sig = tuple(sorted(i["id"] for i in items))
            if sig in seen_sigs:
                continue
            seen_sigs.add(sig)
            # Price handling: treat None as 0
            price = sum((p.get("price") or 0) for p in items)
            if budget and price > budget:
                continue
            total, breakdown = score_outfit(items, palette, twin, style_axes)
            results.append({
                "id": "S-" + "-".join(p["id"] for p in items),
                "items": items,
                "score": total,
                "breakdown": breakdown,
                "price": price,
            })
        results.sort(key=lambda x: -x["score"])
        self._json(results[:6])

    def _handle_vision(self, data):
        if not GEMINI_KEY:
            self._json({"error": "GEMINI_API_KEY not configured", "stub": True}, 503)
            return
        # Real Gemini call would go here. Example structure:
        # POST https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=...
        self._json({
            "status": "proxy_ready",
            "model": "gemini-1.5-flash",
            "note": "Key is server-side. Implement full generateContent call with image base64 when ready.",
            "items": []
        })

    def _handle_photos(self, data):
        token = data.get("access_token")
        if not token:
            self._json({"error": "access_token required", "auth_url": "/api/auth/google/start"}, 401)
            return
        # Real call: POST https://photoslibrary.googleapis.com/v1/mediaItems:search
        # body: {"filters": {"contentFilter": {"includedContentCategories": ["FASHION"]}}}
        self._json({
            "status": "proxy_ready",
            "category": "FASHION",
            "note": "Send access_token from OAuth. Real mediaItems.search not executed until token is valid.",
            "mediaItems": []
        })

    def _handle_affiliate(self, data):
        if not AFFILIATE_KEY:
            self._json({"error": "AFFILIATE_API_KEY not configured", "stub": True}, 503)
            return
        query = data.get("q", "")
        self._json({
            "status": "proxy_ready",
            "query": query,
            "note": "Affiliate network call (Impact/CJ/etc.) would use AFFILIATE_API_KEY server-side.",
            "products": []
        })

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
