"""Failed protected requests must be a single 401 and must not leak file bytes."""
import json

from http_util import assert_single_response, exchange, json_body

UNAUTHORIZED = {
    "error": "unauthorized",
    "hint": "Send Authorization: Bearer <key> or X-API-Key",
}


def test_static_page_is_public_when_api_key_is_set(auth_server):
    raw, parsed = exchange(auth_server.port, "GET", "/sovereign-lens-v2.html")
    assert_single_response(parsed, 200)
    assert parsed["headers"]["content-type"].startswith("text/html")
    assert parsed["body"].startswith(b"<!DOCTYPE html>")
    assert b"unauthorized" not in parsed["body"].lower()
    assert b'"error"' not in parsed["body"]
    assert b"SOVEREIGN" in parsed["body"]
    # The historical bug glued this JSON onto the front of the HTML file.
    assert not raw.startswith(b"HTTP/1.0 401")
    assert not raw.startswith(b"HTTP/1.1 401")


def test_index_is_the_lens_page_without_credentials(auth_server):
    _, parsed = exchange(auth_server.port, "GET", "/")
    assert_single_response(parsed, 200)
    assert b"sovereign lens" in parsed["body"].lower()
    assert b"/api/products" in parsed["body"]
    assert b"Offline fallback" in parsed["body"]


def test_failed_api_get_is_one_json_401(auth_server):
    _, parsed = exchange(auth_server.port, "GET", "/api/products")
    assert_single_response(parsed, 401)
    assert parsed["headers"]["content-type"].startswith("application/json")
    assert json_body(parsed) == UNAUTHORIZED
    folded = parsed["body"].lower()
    assert b"<html" not in folded
    assert b"<!doctype" not in folded
    assert b"black tech fleece" not in folded
    assert b"moncler" not in folded


def test_failed_api_post_is_one_json_401(auth_server):
    _, parsed = exchange(
        auth_server.port,
        "POST",
        "/api/compose",
        body=b'{"palette":["black"],"twin_bias":true}',
    )
    assert_single_response(parsed, 401)
    assert json_body(parsed) == UNAUTHORIZED
    assert b"<html" not in parsed["body"].lower()


def test_wrong_bearer_and_wrong_header_do_not_leak(auth_server):
    for headers in (
        {"Authorization": "Bearer wrong"},
        {"X-API-Key": "wrong"},
        {"Authorization": "Basic dGVzdA=="},
    ):
        _, parsed = exchange(auth_server.port, "GET", "/api/archive", headers=headers)
        assert_single_response(parsed, 401)
        assert json_body(parsed)["error"] == "unauthorized"
        assert b"Digga" not in parsed["body"]


def test_traversal_cannot_read_catalog_files(auth_server):
    for path in (
        "/data/products.json",
        "/api/../data/products.json",
        "/docs/../data/archive.json",
        "/backend/server.py",
        "/repo-bootstrap/src/sovereign_closet/canon/identity.py",
    ):
        _, parsed = exchange(auth_server.port, "GET", path)
        assert_single_response(parsed, 404)
        assert json_body(parsed) == {"error": "not_found"}
        assert b"Black Tech Fleece" not in parsed["body"]
        assert b"protected_back_text" not in parsed["body"]
        assert parsed["status_count"] == 1


def test_unknown_api_route_is_json_404_after_auth(auth_server):
    _, parsed = exchange(
        auth_server.port,
        "GET",
        "/api/missing",
        headers={"Authorization": "Bearer test-key"},
    )
    assert_single_response(parsed, 404)
    assert json_body(parsed) == {"error": "not_found"}


def test_options_preflight_is_single_empty_200(auth_server):
    _, parsed = exchange(auth_server.port, "OPTIONS", "/api/compose")
    assert_single_response(parsed, 200)
    assert parsed["body"] == b""
    allow = parsed["headers"]["access-control-allow-headers"].lower()
    assert "authorization" in allow
    assert "x-api-key" in allow
