"""Smoke coverage for catalogs, compose, twin prompts, and the Lens page contract."""
import json
import os

from http_util import assert_single_response, exchange, json_body

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    with open(os.path.join(APP_ROOT, "data", name), encoding="utf-8") as handle:
        return json.load(handle)


def test_open_mode_serves_canonical_catalogs(open_server):
    products = _load("products.json")
    archive = _load("archive.json")
    _, product_response = exchange(open_server.port, "GET", "/api/products")
    _, archive_response = exchange(open_server.port, "GET", "/api/archive")
    assert_single_response(product_response, 200)
    assert_single_response(archive_response, 200)
    assert json_body(product_response) == products
    assert json_body(archive_response) == archive
    # ZIP catalog is the superset of the earlier 20-item seed.
    assert len(products) >= 55
    assert len(archive) >= 31
    ids = {row["id"] for row in products}
    assert "P001" in ids and "P021" in ids

    _, status = exchange(open_server.port, "GET", "/api/status")
    assert_single_response(status, 200)
    payload = json_body(status)
    assert payload["auth_required"] is False
    assert payload["static_auth"] is False
    assert payload["products"] == len(products)
    assert payload["archive"] == len(archive)
    assert payload["version"] == "0.4.0"


def test_bearer_and_x_api_key_both_authorize(auth_server):
    _, by_bearer = exchange(
        auth_server.port,
        "GET",
        "/api/products",
        headers={"Authorization": "Bearer test-key"},
    )
    _, by_header = exchange(
        auth_server.port,
        "GET",
        "/api/archive",
        headers={"X-API-Key": "test-key"},
    )
    assert_single_response(by_bearer, 200)
    assert_single_response(by_header, 200)
    assert json_body(by_bearer)[0]["id"] == "P001"
    assert json_body(by_header)[0]["id"] == "DD-01"

    _, status = exchange(
        auth_server.port,
        "GET",
        "/api/status",
        headers={"Authorization": "Bearer test-key"},
    )
    assert json_body(status)["auth_required"] is True


def test_compose_and_twin_prompt(open_server):
    _, composed = exchange(
        open_server.port,
        "POST",
        "/api/compose",
        body=json.dumps(
            {
                "query": "moncler maya",
                "palette": ["black", "charcoal", "silver"],
                "twin_bias": True,
                "owned_only": False,
            }
        ).encode(),
    )
    assert_single_response(composed, 200)
    looks = json_body(composed)
    assert 1 <= len(looks) <= 6
    first = looks[0]
    assert first["source"] == "backend"
    assert isinstance(first["score"], float)
    assert "twin_bonus" in first["breakdown"]
    blob = json.dumps(looks).lower()
    assert "moncler" in blob or "maya" in blob
    types = {item["product_type"] for item in first["items"]}
    assert {"top", "bottom", "footwear"} <= types

    _, owned = exchange(
        open_server.port,
        "POST",
        "/api/compose",
        body=json.dumps({"owned_only": True, "palette": ["black"], "budget_max": 400}).encode(),
    )
    for look in json_body(owned):
        assert look["price"] <= 400
        assert all(item["owned"] for item in look["items"])

    _, twin = exchange(
        open_server.port,
        "POST",
        "/api/twin-prompt",
        body=json.dumps(
            {"tunnels": True, "frames": True, "physique": True, "tattoos": False, "notes": "silver only"}
        ).encode(),
    )
    assert_single_response(twin, 200)
    prompt = json_body(twin)
    assert prompt["source"] == "backend"
    assert "4-inch stretched earlobes" in prompt["positive"]
    assert "thick black acetate" in prompt["positive"]
    assert "silver only" in prompt["positive"]
    assert "neck script" not in prompt["positive"]
    assert "small ears" in prompt["negative"]

    _, quiet = exchange(
        open_server.port,
        "POST",
        "/api/twin-prompt",
        body=json.dumps({"tunnels": False, "frames": False, "physique": False, "tattoos": False}).encode(),
    )
    quiet_prompt = json_body(quiet)["positive"]
    assert "tunnels" not in quiet_prompt
    assert "acetate" not in quiet_prompt


def test_outfit_system_endpoints(open_server):
    items = _load("outfit_system_items.json")
    summary = _load("outfit_system_summary.json")
    _, item_response = exchange(open_server.port, "GET", "/api/outfit-items")
    _, summary_response = exchange(open_server.port, "GET", "/api/outfit-system")
    assert_single_response(item_response, 200)
    assert_single_response(summary_response, 200)
    assert json_body(summary_response) == summary
    assert json_body(item_response) == items[:200]
    assert len(json_body(item_response)) == 200


def test_malformed_compose_body_is_still_one_json_response(open_server):
    _, parsed = exchange(open_server.port, "POST", "/api/compose", body=b"not-json")
    assert_single_response(parsed, 200)
    assert isinstance(json_body(parsed), list)


def test_lens_frontend_contract(open_server):
    _, page = exchange(open_server.port, "GET", "/sovereign-lens-v2.html")
    assert_single_response(page, 200)
    html = page["body"].decode()
    for needle in (
        "/api/products",
        "/api/archive",
        "/api/compose",
        "/api/twin-prompt",
        "Authorization",
        "X-API-Key",
        "Offline fallback",
        "SEED_PRODUCTS",
        "catalog-status",
        "Placeholder only",
    ):
        assert needle in html
    # Embedded seed remains for offline use and is not the canonical 55-item catalog.
    assert html.count('id:"P001"') == 1 or 'id:"P001"' in html
    assert "P021" not in html

    _, ui = exchange(open_server.port, "GET", "/backend-ui.html")
    assert_single_response(ui, 200)
    backend_ui = ui["body"].decode()
    assert "/api/compose" in backend_ui
    assert "/api/twin-prompt" in backend_ui
    assert "X-API-Key" in backend_ui

    _, guide = exchange(open_server.port, "GET", "/docs/OUTFIT-GUIDE.md")
    assert_single_response(guide, 200)
    assert b"Formula 1" in guide["body"]


def test_normalize_path_blocks_dot_segments():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "sovereign_lens_server", os.path.join(APP_ROOT, "backend", "server.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.normalize_path("/api/../data/products.json") == "/data/products.json"
    assert module.normalize_path("//docs//API-AUTH.md") == "/docs/API-AUTH.md"
    assert module.static_allowed("/data/products.json") is False
    assert module.static_allowed("/sovereign-lens-v2.html") is True
    assert module.resolve_static("/data/products.json") is None
